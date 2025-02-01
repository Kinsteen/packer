import json
import logging

from packer import cutie
from packer.api import get

logger = logging.getLogger(__name__)


def select_version(mod_slug, version_number, chosen_urls=set()):
    mod = get(f"https://api.modrinth.com/v2/project/{mod_slug}")
    version = get(f"https://api.modrinth.com/v2/project/{mod_slug}/version/{version_number}")
    loaders = json.dumps(version["loaders"])
    game_versions = json.dumps(version["game_versions"])
    if version is not None:
        chosen_urls.add(version["files"][0]["url"])

        for dep in version["dependencies"]:
            if dep["dependency_type"] == "required":
                dep_mod = get(f"https://api.modrinth.com/v2/project/{dep['project_id']}")
                dep_versions = get(f"https://api.modrinth.com/v2/project/{dep_mod['slug']}/version?loaders={loaders}&game_versions={game_versions}")
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
                            f"Mod '{mod['title']}' version '{version['name']}' requires mod '{dep_mod['title']}' with version ID '{dep["version_id"]}', but it wasn't found in the search."
                        )
                        logger.error(
                            f"API URL searched: https://api.modrinth.com/v2/project/{dep['project_id']}/version?loaders={loaders}&game_versions={game_versions}"
                        )
                        return False
                    elif len(next_versions) == 1:
                        chosen_urls.add(next_versions[0]["files"][0]["url"])
                        select_version(dep_mod["slug"], next_versions[0]["version_number"], chosen_urls)
                    else:  # More than one newer version
                        logger.info(
                            f"Mod '{mod['title']}' requires the version '{next_versions[-1]['name']}' for mod '{dep_mod['title']}'. Here are more up to date versions that could work."
                        )
                        choice = cutie.select(list(map(lambda version: version["version_number"], next_versions)), clear_on_confirm=True)
                        chosen_urls.add(next_versions[choice]["files"][0]["url"])
                        select_version(dep_mod["slug"], next_versions[choice]["version_number"], chosen_urls)
                else:
                    logger.info(
                        f"Mod '{mod['title']}' requires the mod '{dep_mod['title']}', but doesn't specify the version. Here are the last 5 versions that matches the loaders and the game versions."
                    )
                    choice = cutie.select(list(map(lambda version: version["version_number"], dep_versions[0:5])), clear_on_confirm=True)
                    chosen_urls.add(dep_versions[choice]["files"][0]["url"])
                    select_version(dep_mod["slug"], dep_versions[choice]["version_number"], chosen_urls)

    else:
        logger.error(f"Cannot find version '{version_number}' for mod '{mod['title']}'.")
        return False

    return True


def modrinth_dep(url):
    mod_slug = url.split("/")[-3]
    version_number = url.split("/")[-1]

    chosen_urls = set()

    success = select_version(mod_slug, version_number, chosen_urls)

    if success:
        for chosen_url in chosen_urls:
            logger.info(chosen_url)
    return
