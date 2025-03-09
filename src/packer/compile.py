import hashlib
import json
import logging
import os
import zipfile
from pathlib import Path

import requests

from packer.config import get_from_cache, open_config

logger = logging.getLogger(__name__)


def get_sha1(data):
    hash = hashlib.sha1()
    hash.update(data)
    return hash.hexdigest()


def get_sha512(data):
    hash = hashlib.sha512()
    hash.update(data)
    return hash.hexdigest()


def read_or_download(name, url):
    cache_path = Path(".cache/" + name)

    if not cache_path.exists():
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


def compile():
    modrinth_index = open_config()
    for file in modrinth_index["files"]:
        name = file["downloads"][0].split("/")[-1]

        # Remove keys that are not modrinth.index.json standard
        if "type" not in file:
            file_type = "MOD"
        else:
            file_type = file["type"]
            del file["type"]

        if "project_url" in file:
            del file["project_url"]

        if file_type == "MOD":
            file["path"] = "mods/" + name
        elif file_type == "RESOURCE_PACK":
            file["path"] = "resourcepacks/" + name
        elif file_type == "SHADER":
            file["path"] = "shaderpacks/" + name

        path = file["path"]
        url = file["downloads"][0]

        if "hashes" not in file:
            file["hashes"] = {}
            file["hashes"]["sha1"] = get_from_cache(path, "sha1", lambda: get_sha1(read_or_download(path, url)))
            file["hashes"]["sha512"] = get_from_cache(path, "sha512", lambda: get_sha512(read_or_download(path, url)))

        if "fileSize" not in file or file["fileSize"] == 0:
            file["fileSize"] = get_from_cache(path, "size", lambda: len(read_or_download(path, url)))

    with open("modrinth.index.json", "w") as output:
        output.write(json.dumps(modrinth_index, indent=4))

    logger.info("Zipping pack...")
    pack_name = f"{modrinth_index["name"].replace(" ", "-")}-{modrinth_index["versionId"].replace(" ", "-")}.mrpack"
    with zipfile.ZipFile(pack_name, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=3) as zip:
        zip.writestr("modrinth.index.json", json.dumps(modrinth_index, indent=4))
        add_folder_to_zip(zip, "overrides")
