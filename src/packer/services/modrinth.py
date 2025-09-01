import json
import logging

import pprint

from packer import cutie
from packer.config import open_config, persist_config
from packer.api import get

logger = logging.getLogger(__name__)


def mod_and_version_to_dict(mod, version):
    ret = {
        "project_url": f"https://modrinth.com/mod/{mod['slug']}",
        "downloads": [version["files"][0]["url"]],
        "env": {}
    }

    if mod['project_type'] == 'mod':
        pass
    elif mod['project_type'] == 'resourcepack':
        ret['type'] = 'RESOURCE_PACK'
    elif mod['project_type'] == 'shader':
        ret['type'] = 'SHADER'

    if mod['client_side'] == 'unsupported':
        ret['env']['client'] = 'unsupported'
    else:
        ret['env']['client'] = 'required'

    if mod['server_side'] == 'unsupported':
        ret['env']['server'] = 'unsupported'
    else:
        ret['env']['server'] = 'required'

    return ret

def select_version(mod_slug, version_id, chosen_urls=list(), seen_mods=set()):
    mod = get(f"https://api.modrinth.com/v2/project/{mod_slug}")
    version = get(f"https://api.modrinth.com/v2/project/{mod_slug}/version/{version_id}")
    loaders = json.dumps(version["loaders"])
    game_versions = json.dumps(version["game_versions"])
    if version is not None:
        chosen_urls.append(mod_and_version_to_dict(mod, version))
        seen_mods.add(mod_slug)

        for dep in version["dependencies"]:
            if dep["dependency_type"] == "required":
                dep_mod = get(f"https://api.modrinth.com/v2/project/{dep['project_id']}")
                if dep_mod['slug'] in seen_mods:
                    continue
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
                        select_version(dep_mod["slug"], next_versions[0]["id"], chosen_urls, seen_mods=seen_mods)
                    else:  # More than one newer version
                        logger.info(
                            f"Mod '{mod['title']}' requires the version '{next_versions[-1]['name']}' for mod '{dep_mod['title']}'. Here are more up to date versions that could work."
                        )
                        choice = cutie.select(list(map(lambda version: version["name"], next_versions)), clear_on_confirm=True)
                        select_version(dep_mod["slug"], next_versions[choice]["id"], chosen_urls, seen_mods=seen_mods)
                else:
                    logger.info(
                        f"Mod '{mod['title']}' requires the mod '{dep_mod['title']}', but doesn't specify the version. Here are the last 5 versions that matches the loaders and the game versions."
                    )
                    choice = cutie.select(list(map(lambda version: version["name"], dep_versions[0:5])), clear_on_confirm=True)
                    select_version(dep_mod["slug"], dep_versions[choice]["id"], chosen_urls, seen_mods=seen_mods)

    else:
        logger.error(f"Cannot find version '{version_id}' for mod '{mod['title']}'.")
        return False

    return True


def modrinth_dep(url):
    mod_slug = url.split("/")[-3]
    version_number = url.split("/")[-1]

    chosen_urls = list()

    success = select_version(mod_slug, version_number, chosen_urls)

    if success:
        for chosen_url in chosen_urls:
            logger.info(chosen_url)
    return

def modrinth_add(slugs):
    packer_config = open_config()
    minecraft_version = packer_config['dependencies']['minecraft']
    chosen_urls = list()
    seen_mods = set()

    for slug in slugs:
        mod = get(f'https://api.modrinth.com/v2/project/{slug}')
        mod_versions = get(f'https://api.modrinth.com/v2/project/{slug}/version?loaders=["neoforge"]&game_versions=["{minecraft_version}"]')
        logger.info(f"Choose a version for '{mod['title']}':")
        choice = cutie.select(list(map(lambda version: version["name"], mod_versions)), clear_on_confirm=True)
        select_version(slug, mod_versions[choice]['id'], chosen_urls, seen_mods=seen_mods)

    for new_file in chosen_urls:
        if new_file not in packer_config['files']:
            packer_config['files'].append(new_file)

    persist_config(packer_config)

    logger.info("Added mods to config!")
