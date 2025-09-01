import json
import logging

import requests

import packer.cutie as cutie
from packer.api import get
from packer.config import open_config, persist_config
from packer.services.provider import ModProvider

logger = logging.getLogger(__name__)


def cat_to_classid(cat) -> str:
    table = {
        "mc-mods": 6,
        "texture-packs": 12,
        "shaders": 6552,
    }
    return table[cat]


def classid_to_cat(classid) -> str:
    table = {
        "6": "mc-mods",
        "12": "texture-packs",
        "6552": "shaders",
    }
    return table[str(classid)]


def mod_and_version_to_dict(mod, version):
    ret = {
        "slug": mod["slug"],
        "version_id": version["id"],
        "project_url": mod["links"]["websiteUrl"],
        "downloads": [version["downloadUrl"]],
        "env": {
            "client": "required",
            "server": "required",
        },
    }

    # if mod["project_type"] == "mod":
    #     pass
    # elif mod["project_type"] == "resourcepack":
    #     ret["type"] = "RESOURCE_PACK"
    # elif mod["project_type"] == "shader":
    #     ret["type"] = "SHADER"

    return ret


class CurseforgeProvider(ModProvider):
    @staticmethod
    def search_slug(slug):
        return super().search_slug(slug)

    @staticmethod
    def get_download_link(slug, version):
        return super().get_download_link(slug, version)

    @staticmethod
    def resolve_dependencies(mod_id, file_id: str, _current_list=None):
        packer_config = open_config()
        minecraft_version = packer_config["dependencies"]["minecraft"]
        if "neoforge" in packer_config["dependencies"]:
            mod_loader = 6
        elif "fabric" in packer_config["dependencies"]:
            mod_loader = 4
        elif "forge" in packer_config["dependencies"]:
            mod_loader = 1

        if not mod_loader:
            raise RuntimeError("Can't find modloader in packer config.")

        base_mod = get(f"https://api.curse.tools/v1/cf/mods/{mod_id}")["data"]
        base_file = get(f"https://api.curse.tools/v1/cf/mods/{mod_id}/files/{file_id}")["data"]
        _current_list.append(mod_and_version_to_dict(base_mod, base_file))

        for dep in base_file["dependencies"]:
            dep_mod = get(f"https://api.curse.tools/v1/cf/mods/{dep['modId']}")["data"]

            seen = list(map(lambda mod: mod["slug"], _current_list))
            if dep_mod["slug"] in seen:
                continue  # Skip already added mod

            should_download = False
            if dep["relationType"] == 2:  # TODO latest
                should_download = cutie.prompt_yes_or_no(f"Found optional mod '{dep_mod['name']}' for '{base_mod['name']}'. Download?")
            elif dep["relationType"] == 3:
                should_download = True

            if should_download:
                files = get(f"https://api.curse.tools/v1/cf/mods/{dep['modId']}/files?gameVersion={minecraft_version}&modLoaderType={mod_loader}")[
                    "data"
                ]
                if len(files) == 0:
                    if dep["relationType"] == 3:
                        logger.error(
                            f"Mod '{base_mod['name']}' version '{base_file['name']}' requires mod '{dep_mod['name']}', but we couldn't find any matching version for our modloader and Minecraft version."
                        )
                        return False
                    elif dep["relationType"] == 2:
                        # Optional, we just skip it
                        continue

                choice = cutie.select(list(map(lambda file: file["fileName"], files)))
                logger.info(f"Chosen {files[choice]['displayName']}")
                CurseforgeProvider.resolve_dependencies(files[choice]["modId"], files[choice]["id"], _current_list)
        return _current_list


def curseforge_add(slugs: str, save: bool):
    packer_config = open_config()
    minecraft_version = packer_config["dependencies"]["minecraft"]
    if "neoforge" in packer_config["dependencies"]:
        mod_loader = 6
    elif "fabric" in packer_config["dependencies"]:
        mod_loader = 4
    elif "forge" in packer_config["dependencies"]:
        mod_loader = 1

    if not mod_loader:
        raise RuntimeError("Can't find modloader in packer config.")

    chosen_mods = list()
    for slug in slugs:
        mod = get(f"https://api.curse.tools/v1/cf/mods/search?gameId=432&classId=6&slug={slug}")
        if mod is None:
            logger.warning(f"Can't find mod '{slug}'.")
        mod = mod["data"][0]
        mod_versions = get(f"https://api.curse.tools/v1/cf/mods/{mod['id']}/files?gameVersion={minecraft_version}&modLoaderType={mod_loader}")["data"]
        logger.info(f"Choose a version for '{mod['name']}':")
        choice = cutie.select(list(map(lambda version: version["fileName"], mod_versions)), clear_on_confirm=True)
        logger.info(f"Selected version '{mod_versions[choice]['fileName']}'")
        CurseforgeProvider.resolve_dependencies(mod["id"], mod_versions[choice]["id"], _current_list=chosen_mods)

    if save:
        for new_file in chosen_mods:
            if new_file not in packer_config["files"]:
                packer_config["files"].append(new_file)

        persist_config(packer_config)
        logger.info("Added mods to config!")
    else:
        logger.info(json.dumps(chosen_mods, indent=4))



def curseforge_url(url: str):
    session = requests.Session()
    slug = url.split("/")[-3]
    category_slug = url.split("/")[-4]
    search_results = session.get(f"https://api.curse.tools/v1/cf/mods/search?gameId=432&classId={cat_to_classid(category_slug)}&slug={slug}").json()[
        "data"
    ]
    if len(search_results) == 0:
        logger.error("Can't find the file on Curseforge, in mods, resource packs or shader packs.")
        logger.error("Is the URL correct? https://www.curseforge.com/minecraft/[mc-mods, texture-packs, shaders]/<slug>/files/<file id>")
        return 1

    mod_id = search_results[0]["id"]
    file_id = url.split("/")[-1]

    try:
        file = session.get(f"https://api.curse.tools/v1/cf/mods/{mod_id}/files/{file_id}").json()["data"]
        logger.info(file["downloadUrl"])
    except Exception:
        logger.error("File seems to not be found.")
        logger.error("Is the URL correct? https://www.curseforge.com/minecraft/[mc-mods, texture-packs, shaders]/<slug>/files/<file id>")
        return 1


def get_project_url(mod_id):
    mod = get(f"https://api.curse.tools/v1/cf/mods/{mod_id}")["data"]
    try:
        return f"https://www.curseforge.com/minecraft/{classid_to_cat(mod['classId'])}/{mod['slug']}"
    except Exception:
        return None
