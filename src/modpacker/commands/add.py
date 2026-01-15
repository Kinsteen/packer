import json
import logging

import questionary

from modpacker.config import open_config, persist_config
from modpacker.services.provider import ModProvider

logger = logging.getLogger(__name__)


def add(provider: ModProvider, slugs, save, latest):
    packer_config = open_config()
    minecraft_version = packer_config["dependencies"]["minecraft"]
    if "neoforge" in packer_config["dependencies"]:
        mod_loader = "neoforge"
    elif "fabric" in packer_config["dependencies"]:
        mod_loader = "fabric"
    elif "forge" in packer_config["dependencies"]:
        mod_loader = "forge"

    chosen_mods = list()

    for slug in slugs:
        if slug.startswith("http"):
            slug = slug.split("/")[-1]
        mod = provider.get_mod(slug)
        if mod is None:
            continue
        mod_version = provider.pick_mod_version(mod, minecraft_version, mod_loader, latest)
        provider.resolve_dependencies(mod["id"], mod_version["id"], latest, _current_list=chosen_mods)

    if save:
        for new_file in chosen_mods:
            added = False
            for idx, mod in enumerate(packer_config["files"]):
                if new_file["slug"] == mod["slug"]:
                    if new_file['downloads'][0] != packer_config['files'][idx]['downloads'][0]:
                        logger.info(f"Mod {mod['slug']} already exists in the pack, changing in place")
                        logger.info(f"New URL: {new_file['downloads'][0]}")
                        logger.info(f"Old URL: {packer_config['files'][idx]['downloads'][0]}")
                        should_replace = questionary.confirm("Replace?").ask()
                        if should_replace:
                            packer_config["files"][idx] = new_file
                    added = True
            if not added:
                if new_file not in packer_config["files"]:
                    packer_config["files"].append(new_file)

        persist_config(packer_config)
        logger.info("Added mods to config!")
    else:
        logger.info(json.dumps(chosen_mods, indent=4))
