import hashlib
import json
import logging
import os
import zipfile
from pathlib import Path

import requests

from packer.api import get, post
from packer.config import get_from_cache, open_config

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


def add_folder_to_zip(zipf, folder_name, base_folder="overrides"):
    for root, _, files in os.walk(folder_name):
        for file in files:
            file_path = os.path.join(root, file)
            zip_file_path = file_path
            zipf.write(file_path, zip_file_path)


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


def compile():
    modrinth_index = open_config()
    for file in modrinth_index["files"]:
        # Remove keys that are not modrinth.index.json standard
        if "type" in file:
            del file["type"]

        if "project_url" in file:
            del file["project_url"]

        path = get_path(file)
        url = file["downloads"][0]

        if "hashes" not in file or "sha1" not in file["hashes"] or "sha256" not in file["hashes"] or "sha512" not in file["hashes"]:
            file["hashes"] = {}
            file["hashes"]["sha1"] = get_from_cache(path, "sha1", lambda: get_sha1(read_or_download(path, url)))
            file["hashes"]["sha256"] = get_from_cache(path, "sha256", lambda: get_sha256(read_or_download(path, url)))
            file["hashes"]["sha512"] = get_from_cache(path, "sha512", lambda: get_sha512(read_or_download(path, url)))

        if "fileSize" not in file or file["fileSize"] == 0:
            file["fileSize"] = get_from_cache(path, "size", lambda: len(read_or_download(path, url)))

    with open("modrinth.index.json", "w") as output:
        output.write(json.dumps(modrinth_index, indent=4))

    logger.info("Zipping pack...")
    pack_name = f"{modrinth_index['name'].replace(' ', '-')}-{modrinth_index['versionId'].replace(' ', '-')}.mrpack"
    with zipfile.ZipFile(pack_name, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=3) as zip:
        zip.writestr("modrinth.index.json", json.dumps(modrinth_index, indent=4))
        add_folder_to_zip(zip, "overrides")
