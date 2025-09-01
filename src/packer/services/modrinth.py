import json
import logging
import re

from packer import cutie
from packer.api import get
from packer.config import open_config, persist_config
from packer.services.provider import ModProvider

logger = logging.getLogger(__name__)


def mod_and_version_to_dict(mod, version):
    ret = {"project_url": f"https://modrinth.com/mod/{mod['slug']}", "downloads": [version["files"][0]["url"]], "env": {}}

    if mod["project_type"] == "mod":
        pass
    elif mod["project_type"] == "resourcepack":
        ret["type"] = "RESOURCE_PACK"
    elif mod["project_type"] == "shader":
        ret["type"] = "SHADER"

    if mod["client_side"] == "unsupported":
        ret["env"]["client"] = "unsupported"
    else:
        ret["env"]["client"] = "required"

    if mod["server_side"] == "unsupported":
        ret["env"]["server"] = "unsupported"
    else:
        ret["env"]["server"] = "required"

    return ret


def version_text_from_version(version):
    if version["version_number"] == version["name"]:
        return version["version_number"]
    if version["version_number"] in version["name"]:
        return version["name"]
    return version["version_number"] + " / " + version["name"]


class ModrinthProvider(ModProvider):
    full_version_url_pattern = re.compile(r"https://modrinth.com/mod/([^/]+)/version/([^/]+)")

    def search_slug(slug, loader="neoforge"):
        packer_config = open_config()
        minecraft_version = packer_config["dependencies"]["minecraft"]
        mod = get(f"https://api.modrinth.com/v2/project/{slug}")
        if mod is None:
            return None
        mod_versions = get(f'https://api.modrinth.com/v2/project/{slug}/version?loaders=["{loader}"]&game_versions=["{minecraft_version}"]')
        logger.info(f"Choose a version for '{mod['title']}':")
        choice = cutie.select(list(map(lambda version: version["name"], mod_versions)), clear_on_confirm=True)
        mod_version = mod_versions[choice]

        ret = {
            "slug": slug,
            "version_id": mod_version["id"],
            "project_url": f"https://modrinth.com/mod/{slug}",
            "downloads": [ModrinthProvider.get_download_link(slug, mod_version)],
            "env": {},
        }

        if mod["client_side"] == "unsupported":
            ret["env"]["client"] = "unsupported"
        else:
            ret["env"]["client"] = "required"

        if mod["server_side"] == "unsupported":
            ret["env"]["server"] = "unsupported"
        else:
            ret["env"]["server"] = "required"

        return ret

    def resolve_dependencies(mod_id, version_id, _current_list=None) -> list[dict]:
        if _current_list is None:
            print("creating new list")
            _current_list = []
        mod = get(f"https://api.modrinth.com/v2/project/{mod_id}")
        if mod is None:
            return _current_list

        # Early return if mod already exists
        # TODO we should instead do a proper DAG with dependencies resolution and conflicts
        # if conflicting versions required
        for selected_mod in _current_list:
            if selected_mod["slug"] == mod["slug"]:
                return _current_list

        mod_version = get(f"https://api.modrinth.com/v2/project/{mod_id}/version/{version_id}")
        loaders = json.dumps(mod_version["loaders"])
        game_versions = json.dumps(mod_version["game_versions"])

        _current_list.append(mod_and_version_to_dict(mod, mod_version))

        for dep in mod_version["dependencies"]:
            dep_mod = get(f"https://api.modrinth.com/v2/project/{dep['project_id']}")
            if dep_mod is None:
                continue
            seen = list(map(lambda mod: mod["slug"], _current_list))
            if dep_mod["slug"] in seen:
                continue  # Skip already added mod

            dep_versions = get(f"https://api.modrinth.com/v2/project/{dep_mod['slug']}/version?loaders={loaders}&game_versions={game_versions}")

            # No suitable versions has been found, continuing with another dep
            if len(dep_versions) == 0:
                if dep["dependency_type"] == "required":
                    logger.error("Couldn't find any version that fulfill the requirement.")
                    logger.error(
                        f"Mod '{mod['title']}' version '{mod_version['name']}' requires mod '{dep_mod['title']}', but we couldn't find any matching version for our modloader and Minecraft version."
                    )
                    return False
                elif dep["dependency_type"] == "optional":
                    # Optional, we just skip it
                    continue

            should_download = False
            if dep["dependency_type"] == "required":
                should_download = True
            elif dep["dependency_type"] == "optional":
                should_download = cutie.prompt_yes_or_no(f"Found optional mod '{dep_mod['title']}' for '{mod['title']}'. Download?")

            if should_download:
                if dep["version_id"] is not None:
                    # Fetch all versions that are later or equal to the version required.
                    next_versions = []
                    for dep_version in dep_versions:
                        next_versions.append(dep_version)
                        if dep_version["id"] == dep["version_id"]:
                            break
                    if len(next_versions) == 0:
                        logger.error("Couldn't find any version that fulfill the requirement.")
                        logger.error(
                            f"Mod '{mod['title']}' version '{mod_version['name']}' requires mod '{dep_mod['title']}' with version ID '{dep["version_id"]}', but it wasn't found in the search."
                        )
                        logger.error(
                            f"API URL searched: https://api.modrinth.com/v2/project/{dep['project_id']}/version?loaders={loaders}&game_versions={game_versions}"
                        )
                        return False
                    elif len(next_versions) == 1:
                        ModrinthProvider.resolve_dependencies(dep_mod["id"], next_versions[0]["id"], _current_list)
                    else:  # More than one newer version
                        logger.info(
                            f"Mod '{mod['title']}' requires the version '{next_versions[-1]['name']}' for mod '{dep_mod['title']}'. Here are more up to date versions that could work."
                        )
                        choice = cutie.select(list(map(version_text_from_version, next_versions)), clear_on_confirm=True)
                        logger.info(f"Selected version '{version_text_from_version(next_versions[choice])}'")
                        ModrinthProvider.resolve_dependencies(dep_mod["id"], next_versions[choice]["id"], _current_list)
                else:
                    logger.info(
                        f"Mod '{mod['title']}' requires the mod '{dep_mod['title']}', but doesn't specify the version. Here are the last 5 versions that matches the loaders and the game versions."
                    )
                    choice = cutie.select(list(map(version_text_from_version, dep_versions)), clear_on_confirm=True)
                    logger.info(f"Selected version '{version_text_from_version(dep_versions[choice])}'")
                    ModrinthProvider.resolve_dependencies(dep_mod["id"], dep_versions[choice]["id"], _current_list)
        return _current_list

    def get_download_link(slug, version):
        return version["files"][0]["url"]


def modrinth_add(slugs, save):
    packer_config = open_config()
    minecraft_version = packer_config["dependencies"]["minecraft"]
    chosen_mods = list()

    for slug in slugs:
        mod = get(f"https://api.modrinth.com/v2/project/{slug}")
        mod_versions = get(f'https://api.modrinth.com/v2/project/{slug}/version?loaders=["neoforge"]&game_versions=["{minecraft_version}"]')
        logger.info(f"Choose a version for '{mod['title']}':")
        choice = cutie.select(list(map(lambda version: version["name"], mod_versions)), clear_on_confirm=True)
        logger.info(f"Selected version '{version_text_from_version(mod_versions[choice])}'")
        ModrinthProvider.resolve_dependencies(mod["id"], mod_versions[choice]["id"], _current_list=chosen_mods)

    if save:
        for new_file in chosen_mods:
            if new_file not in packer_config["files"]:
                packer_config["files"].append(new_file)

        persist_config(packer_config)
        logger.info("Added mods to config!")
    else:
        logger.info(json.dumps(chosen_mods, indent=4))
