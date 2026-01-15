import hashlib
import json
import logging
import os
import zipfile
from pathlib import Path

import requests

from modpacker.api import get, post
from modpacker.config import get_from_cache, open_config

logger = logging.getLogger(__name__)


def get_sha1(data):
    hash = hashlib.sha1()
    hash.update(data)
    return hash.hexdigest()


def get_sha256(data):
    hash = hashlib.sha256()
    hash.update(data)
    return hash.hexdigest()


def get_sha512(data):
    hash = hashlib.sha512()
    hash.update(data)
    return hash.hexdigest()


def read_or_download(name, url):
    cache_path = Path(".cache/" + name)

    if not cache_path.exists():
        logger.info(f"Downloading {url}")
        remote = requests.get(url)
        if not cache_path.parent.exists():
            os.makedirs(cache_path.parent)
        with open(".cache/" + name, "wb") as f:
            f.write(remote.content)
        return remote.content
    else:
        with open(".cache/" + name, "rb") as f:
            return f.read()


def add_folder_to_zip(zipf: zipfile.ZipFile, folder_name, base_folder="overrides"):
    for root, _, files in os.walk(folder_name):
        for file in files:
            file_path = root + "/" + file
            zip_file_path = file_path
            if zip_file_path not in zipf.NameToInfo: # We don't want to have duplicate files
                zipf.write(file_path, zip_file_path)
            else:
                logger.warning(f"It seems like there is already '{zip_file_path}' in the created zipfile. This can happen if you're trying to override a generated file. Don't do that!")


def add_file_to_zip(zipf, file_name):
    file_path = os.path.relpath(file_name)
    zip_file_path = file_path
    zipf.write(file_path, zip_file_path)


def get_path(file):
    name = file["downloads"][0].split("/")[-1]
    if "type" not in file:
        file_type = "MOD"
    else:
        file_type = file["type"]

    if file_type == "MOD":
        return "mods/" + name
    elif file_type == "RESOURCE_PACK":
        return "resourcepacks/" + name
    elif file_type == "SHADER":
        return "shaderpacks/" + name


def get_slug(file):
    """Get the slug of a mod from its download URL. Is quite expensive, calls should be cached."""
    url = file["downloads"][0]
    if "modrinth.com" in url:
        project_id = url.split("/")[-4]
        mod = get(f"https://api.modrinth.com/v2/project/{project_id}")
        return mod["slug"]
    elif "curse" in url or "forge" in url:
        file_id = url.split("/")[-3].rjust(4, "0") + url.split("/")[-2].rjust(3, "0")
        mod_id = post(
            "https://api.curse.tools/v1/cf/mods/files",
            {"fileIds": [int(file_id)]},
        )["data"][
            0
        ]["modId"]
        mod = get(f"https://api.curse.tools/v1/cf/mods/{mod_id}")["data"]
        return mod["slug"]


def unsup_ini_content(config):
    unsup_ini = """
version=1
preset=minecraft

source_format=packwiz
source={source}
"""
    unsup_content = unsup_ini.format(source=config["source"])
    if "signature" in config:
        unsup_content += "public_key=" + config["signature"]
    return unsup_content.strip()

def get_recommended_lwjgl(minecraft_version: str):
    r = requests.get("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json").json()
    for version in r["versions"]:
        if version["id"] == minecraft_version:
            version_meta = requests.get(version["url"]).json()
            for lib in version_meta["libraries"]:
                if "org.lwjgl:lwjgl-glfw" in lib["name"]:
                    return lib["name"].split(":")[2]


def compile_prism(packer_config):
    pack_name = f"{packer_config['name'].replace(' ', '-')}-{packer_config['versionId'].replace(' ', '-')}-prism.zip"

    mmc_pack = {
        "formatVersion": 1,
        "components": [
            {
                "uid": "org.lwjgl3",
                "version": get_recommended_lwjgl(packer_config["dependencies"]["minecraft"])
            },
            {
                "uid": "net.minecraft",
                "version": packer_config["dependencies"]["minecraft"]
            },
            {
                "uid": "net.neoforged",
                "version": packer_config["dependencies"]["neoforge"]
            },
            {
                "uid": "com.unascribed.unsup",
                "version": packer_config["unsup"]["version"]
            }
        ],
    }

    unsup_latest_release = requests.get(f"https://git.sleeping.town/api/v1/repos/exa/unsup/releases/tags/v{packer_config['unsup']['version']}").json()
    for asset in unsup_latest_release['assets']:
        if asset['name'] == "com.unascribed.unsup.json":
            unsup_patch = requests.get(asset['browser_download_url']).content

    with zipfile.ZipFile(pack_name, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=3) as zip:
        zip.writestr("instance.cfg", "")
        zip.writestr("minecraft/unsup.ini", unsup_ini_content(packer_config["unsup"]))
        zip.writestr("mmc-pack.json", json.dumps(mmc_pack, indent=4))
        zip.writestr("patches/com.unascribed.unsup.json", unsup_patch)

def compile(prism = False):
    packer_config = open_config()

    unsup_config = None
    if "unsup" in packer_config:
        unsup_config = packer_config["unsup"]

    if prism:
        if unsup_config:
            return compile_prism(packer_config)
        else:
            logger.error("Prism export only works if unsup is set in packer_config.json.")
            exit(1)

    for file in packer_config["files"]:
        # Remove keys that are not modrinth.index.json standard
        for key in ["type", "slug", "project_url", "version_id"]:
            if key in file:
                del file[key]

        path = get_path(file)
        file["path"] = path
        url = file["downloads"][0]

        if "hashes" not in file or "sha1" not in file["hashes"] or "sha256" not in file["hashes"] or "sha512" not in file["hashes"]:
            file["hashes"] = {}
            file["hashes"]["sha1"] = get_from_cache(path, "sha1", lambda: get_sha1(read_or_download(path, url)))
            file["hashes"]["sha256"] = get_from_cache(path, "sha256", lambda: get_sha256(read_or_download(path, url)))
            file["hashes"]["sha512"] = get_from_cache(path, "sha512", lambda: get_sha512(read_or_download(path, url)))

        if "fileSize" not in file or file["fileSize"] == 0:
            file["fileSize"] = get_from_cache(path, "size", lambda: len(read_or_download(path, url)))

    with open("modrinth.index.json", "w") as output:
        output.write(json.dumps(packer_config, indent=4))

    logger.info("Zipping pack...")
    pack_name = f"{packer_config['name'].replace(' ', '-')}-{packer_config['versionId'].replace(' ', '-')}.mrpack"
    with zipfile.ZipFile(pack_name, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=3) as zip:
        zip.writestr("modrinth.index.json", json.dumps(packer_config, indent=4))
        if unsup_config:
            logger.info("Generating unsup.ini...")
            zip.writestr("overrides/unsup.ini", unsup_ini_content(unsup_config))

        add_folder_to_zip(zip, "overrides")
