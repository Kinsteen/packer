import logging

import tqdm

import modpacker.services.curseforge as cf
import modpacker.services.modrinth as mr
from modpacker.config import persist_config
from modpacker.log.tqdm_wrapper import tqdm_output
from modpacker.packer_config import PackerConfig

logger = logging.getLogger(__name__)

def update(packer_config: PackerConfig):
    minecraft_version = packer_config.minecraft_version

    data = packer_config.data
    mr_provider = mr.ModrinthProvider(packer_config)
    cf_provider = cf.CurseforgeProvider(packer_config)

    with tqdm_output(tqdm.tqdm(packer_config["files"])) as progress_bar:
        for idx, mod in enumerate(progress_bar):
            if "modrinth" in mod["downloads"][0]:
                provider = mr_provider
            else:
                provider = cf_provider

            mod = provider.get_mod(mod["slug"])
            version = provider.pick_mod_version(mod, minecraft_version, True)
            url = provider.get_download_link(mod["slug"], version)
            if url != data["files"][idx]["downloads"][0]:
                logger.info(f"Found update for {mod['slug']}")
                data["files"][idx]["downloads"][0] = url
                data["files"]["versionId"] = version["id"]

    persist_config(data)
