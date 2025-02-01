import datetime
import json
import logging

import requests

import packer.cutie as cutie
from packer.api import get
from packer.config import open_config

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


def select_dep(mod_id, file_id, latest, version_choice=None, chosen_urls=[], session=None) -> list[str]:
    global modloader_id
    if session is None:
        session = requests.Session()
    base_mod = session.get(f"https://api.curse.tools/v1/cf/mods/{mod_id}").json()["data"]
    base_file = session.get(f"https://api.curse.tools/v1/cf/mods/{mod_id}/files/{file_id}").json()["data"]
    chosen_urls.append(base_file["downloadUrl"])
    logger.info(f"Searching deps for {base_mod['name']} / {base_file['displayName']}")
    if version_choice is None:
        logger.info("Choose game version to search:")
        version_choice = base_file["gameVersions"][cutie.select(base_file["gameVersions"])]

    for dep in base_file["dependencies"]:
        dep_mod = session.get(f"https://api.curse.tools/v1/cf/mods/{dep['modId']}").json()["data"]

        should_download = False
        if dep["relationType"] == 2 and not latest:
            should_download = cutie.prompt_yes_or_no(f"Found optional mod '{dep_mod['name']}' for '{base_mod['name']}'. Download?")
        if dep["relationType"] == 3:
            should_download = True

        if should_download:
            r = session.get(
                f"https://api.curse.tools/v1/cf/mods/{dep['modId']}/files?gameVersion={version_choice}&modLoaderType={get_modloader_id()}"
            )
            text_choices = []
            urls = []
            if len(r.json()["data"]) == 0:
                logger.warning(
                    f"No files found for required dependency '{dep_mod['name']}'. Either it's not declared as compatible with the current version ({version_choice}), "
                    + f"or it's not declared using the correct modloader. You should check here: {get_project_url(dep_mod['id'])}"
                )
                continue
            already_added = False
            for version in r.json()["data"][0:5]:
                text_choices.append(f"{version['fileName']} ({datetime.datetime.strptime(version['fileDate'],'%Y-%m-%dT%H:%M:%S.%fZ')})")
                urls.append(version["downloadUrl"])
                if version["downloadUrl"] in chosen_urls:
                    already_added = True
            if not already_added:
                if latest:
                    choice = 0
                else:
                    choice = cutie.select(text_choices, clear_on_confirm=True)
                file_chosen = r.json()["data"][choice]
                logger.info(f"Chosen {file_chosen['displayName']}")
                chosen_urls.append(file_chosen["downloadUrl"])
                select_dep(
                    dep["modId"],
                    file_chosen["id"],
                    latest,
                    version_choice=version_choice,
                    chosen_urls=chosen_urls,
                )

    return chosen_urls


def curseforge_dep(url: str, latest: bool):
    session = requests.Session()
    slug = url.split("/")[-3]
    r = session.get(f"https://api.curse.tools/v1/cf/mods/search?gameId=432&classId=6&slug={slug}")
    mod_id = r.json()["data"][0]["id"]
    file_id = url.split("/")[-1]

    chosen_urls = select_dep(mod_id, file_id, latest, session=session)

    output = []
    for u in set(chosen_urls):
        output.append({"downloads": [u], "env": {"client": "required", "server": "required"}})
    logger.info(json.dumps(output, indent=4))


def curseforge_url(url: str):
    session = requests.Session()
    slug = url.split("/")[-3]
    category_slug = url.split("/")[-4]
    categories = {
        "mc-mods": 6,
        "texture-packs": 12,
        "shaders": 6552,
    }
    search_results = session.get(f"https://api.curse.tools/v1/cf/mods/search?gameId=432&classId={categories[category_slug]}&slug={slug}").json()[
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


def get_modloader_id():
    if get_modloader_id.modloader_id is None:
        config = open_config()
        if "neoforge" in config["dependencies"]:
            get_modloader_id.modloader_id = 6
        if "fabric" in config["dependencies"]:
            get_modloader_id.modloader_id = 4
        if "forge" in config["dependencies"]:
            get_modloader_id.modloader_id = 1
    return get_modloader_id.modloader_id


get_modloader_id.modloader_id = None


def get_project_url(mod_id):
    mod = get(f"https://api.curse.tools/v1/cf/mods/{mod_id}")["data"]
    try:
        return f"https://www.curseforge.com/minecraft/{classid_to_cat(mod['classId'])}/{mod['slug']}"
    except Exception:
        return None
