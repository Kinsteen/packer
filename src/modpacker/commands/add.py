import json
import logging

import questionary

from modpacker.config import persist_config
from modpacker.packer_config import PackerConfig
from modpacker.services.provider import ModProvider

logger = logging.getLogger(__name__)


def add(packer_config: PackerConfig, provider: ModProvider, slugs, save, latest):
    minecraft_version = packer_config.minecraft_version

    chosen_mods = list()

    for slug in slugs:
        if slug.startswith("http"):
            slug = slug.split("/")[-1]
        if mod := provider.get_mod(slug):
            if mod_version := provider.pick_mod_version(mod, minecraft_version, latest):
                provider.resolve_dependencies(mod["id"], mod_version["id"], latest, _current_list=chosen_mods)

    if save:
        data = packer_config.data
        for new_file in chosen_mods:
            added = False
            for idx, mod in enumerate(data["files"]):
                if new_file["slug"] == mod["slug"]:
                    if new_file['downloads'][0] != data['files'][idx]['downloads'][0]:
                        logger.info(f"Mod {mod['slug']} already exists in the pack, changing in place")
                        logger.info(f"New URL: {new_file['downloads'][0]}")
                        logger.info(f"Old URL: {data['files'][idx]['downloads'][0]}")
                        should_replace = questionary.confirm("Replace?").ask()
                        if should_replace:
                            data["files"][idx] = new_file
                    added = True
            if not added:
                if new_file not in data["files"]:
                    data["files"].append(new_file)

        persist_config(data)
        logger.info("Added mods to config!")
    else:
        logger.info(json.dumps(chosen_mods, indent=4))
    return chosen_mods
