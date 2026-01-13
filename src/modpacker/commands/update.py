import logging

import modpacker.services.curseforge as cf
import modpacker.services.modrinth as mr
from modpacker.config import open_config, persist_config

logger = logging.getLogger(__name__)

def update():
    packer_config = open_config()
    minecraft_version = packer_config["dependencies"]["minecraft"]
    if "neoforge" in packer_config["dependencies"]:
        mod_loader = "neoforge"
    elif "fabric" in packer_config["dependencies"]:
        mod_loader = "fabric"
    elif "forge" in packer_config["dependencies"]:
        mod_loader = "forge"

    for idx, mod in enumerate(packer_config["files"]):
        if "modrinth" in mod["downloads"][0]:
            provider = mr.ModrinthProvider()
        else:
            provider = cf.CurseforgeProvider()

        mod = provider.get_mod(mod["slug"])
        version = provider.pick_mod_version(mod, minecraft_version, mod_loader, True)
        url = provider.get_download_link(version)
        packer_config["files"][idx]["downloads"][0] = url
    
    persist_config(packer_config)
