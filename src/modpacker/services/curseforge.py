import json
import logging

import questionary
import requests

from modpacker.api import get
from modpacker.config import open_config, persist_config
from modpacker.services.provider import ModProvider

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

    if "Client" in version["gameVersions"]:
        ret["env"]["server"] = "unsupported"

    return ret


class CurseforgeProvider(ModProvider):

    def get_mod(self, slug):
        maybe_mod = get(f"https://api.curse.tools/v1/cf/mods/search?gameId=432&classId=6&slug={slug}")
        if maybe_mod is None or len(maybe_mod["data"]) == 0:
            logger.error(f"Can't find mod '{slug}'.")
            return None
        return maybe_mod["data"][0]

    def pick_mod_version(self, mod, minecraft_version, mod_loader, latest=False):
        mod_versions = get(f"https://api.curse.tools/v1/cf/mods/{mod['id']}/files?gameVersion={minecraft_version}&modLoaderType={mod_loader}")["data"]
        if not latest:
            choices = list(map(lambda version: version["fileName"], mod_versions))
            answer = questionary.select(f"What version for version '{mod['name']}'?", choices).ask()
            choice = choices.index(answer)
        else:
            choice = 0
        return mod_versions[choice]

    @staticmethod
    def search_slug(slug):
        return super().search_slug(slug)

    @staticmethod
    def get_download_link(slug, version):
        return super().get_download_link(slug, version)

    def resolve_dependencies(self, mod_id, file_id: str, latest=False, _current_list=None):
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
            if dep["relationType"] == 2 and not latest:
                should_download = questionary.confirm(f"Found optional mod '{dep_mod['name']}' for '{base_mod['name']}'. Download?", default=False, auto_enter=False).ask()
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

                if latest:
                    choice = 0
                else:
                    choices = list(map(lambda file: file["fileName"], files))
                    answer = questionary.select(f"What version for version '{dep_mod['name']}'?", choices).ask()
                    choice = choices.index(answer)
                self.resolve_dependencies(files[choice]["modId"], files[choice]["id"], latest, _current_list)
        return _current_list

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

def get_project_slug(mod_id):
    mod = get(f"https://api.curse.tools/v1/cf/mods/{mod_id}")["data"]
    return mod['slug']
