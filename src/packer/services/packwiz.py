import hashlib
import logging
import os
import shutil

import tomli_w

from packer.compile import get_sha256, get_slug, read_or_download
from packer.config import get_from_cache, open_config

logger = logging.getLogger(__name__)


def convert(output_folder):
    packer_config = open_config()
    os.makedirs(output_folder, exist_ok=True)

    indextoml = {"hash-format": "sha256", "files": []}

    logger.info("Creating metafiles...")

    for file in packer_config["files"]:
        name = file["downloads"][0].split("/")[-1]

        side = "both"
        if file["env"]["server"] == "unsupported":
            side = "client"

        if "type" not in file:
            file_type = "MOD"
        else:
            file_type = file["type"]

        if file_type == "MOD":
            file["path"] = "mods/" + name
        elif file_type == "RESOURCE_PACK":
            file["path"] = "resourcepacks/" + name
        elif file_type == "SHADER":
            file["path"] = "shaderpacks/" + name

        path = file["path"]
        url = file["downloads"][0]

        slug = get_from_cache(path, "slug", lambda: get_slug(file))
        # TODO update property for modrinth and curseforge?
        filetoml = {
            "name": slug,
            "filename": name,
            "side": side,
            "download": {
                "hash-format": "sha256",
                "hash": get_from_cache(path, "sha256", lambda: get_sha256(read_or_download(path, url))),
                "url": file["downloads"][0].replace(" ", "%20").replace("[", "%5B").replace("]", "%5D"),
            },
        }
        os.makedirs(os.path.join(output_folder, os.path.dirname(file["path"])), exist_ok=True)
        new_path = os.path.dirname(path) + "/" + slug + ".pw.toml"  # no os.path.join because we always want slashes
        with open(os.path.join(output_folder, new_path), "wb") as f:
            tomli_w.dump(filetoml, f)

        with open(os.path.join(output_folder, new_path), "rb") as f:
            indextoml["files"].append(
                {
                    "file": new_path,
                    "hash": hashlib.sha256(f.read()).hexdigest(),
                    "metafile": True,
                }
            )

    logger.info("Creating overrides...")

    if os.path.exists("overrides"):
        for root, _, files in os.walk("overrides"):
            for file in files:
                path = os.path.join(root, file)
                destination = os.path.relpath(path, "overrides/")
                os.makedirs(os.path.dirname(os.path.join(output_folder, destination)), exist_ok=True)
                shutil.copy(os.path.join(root, file), os.path.join(output_folder, destination))
                with open(os.path.join(output_folder, destination), "rb") as f:
                    indextoml["files"].append({"file": destination.replace("\\", "/"), "hash": hashlib.sha256(f.read()).hexdigest()})

    with open(os.path.join(output_folder, "index.toml"), "wb") as f:
        tomli_w.dump(indextoml, f)
    with open(os.path.join(output_folder, "index.toml"), "rb") as f:
        index_hash = hashlib.sha256(f.read()).hexdigest()

    packtoml = {
        "name": packer_config["name"],
        "pack-format": "packwiz:1.1.0",
        "version": packer_config["versionId"],
        "index": {"file": "index.toml", "hash-format": "sha256", "hash": index_hash},
        "versions": {},
    }

    for dep in packer_config["dependencies"]:
        packtoml["versions"][dep] = packer_config["dependencies"][dep]

    with open(os.path.join(output_folder, "pack.toml"), "wb") as f:
        tomli_w.dump(packtoml, f)

    logger.info("Done!")
