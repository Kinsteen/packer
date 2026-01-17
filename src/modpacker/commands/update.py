import logging

import modpacker.services.curseforge as cf
import modpacker.services.modrinth as mr
from modpacker.config import persist_config
from modpacker.packer_config import PackerConfig

logger = logging.getLogger(__name__)

def update(packer_config: PackerConfig):
    minecraft_version = packer_config.minecraft_version
    mod_loader = packer_config.mod_loader

    data = packer_config.data

    for idx, mod in enumerate(packer_config["files"]):
        if "modrinth" in mod["downloads"][0]:
            provider = mr.ModrinthProvider()
        else:
            provider = cf.CurseforgeProvider()

        mod = provider.get_mod(mod["slug"])
        version = provider.pick_mod_version(mod, minecraft_version, mod_loader, True)
        url = provider.get_download_link(version)
        data["files"][idx]["downloads"][0] = url

    persist_config(data)
