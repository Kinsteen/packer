import atexit
import logging

import tqdm

from packer.api import get, post
from packer.config import open_config, persist_config
from packer.log.tqdm_wrapper import tqdm_output
from packer.services.curseforge import get_project_url as cf_get_project_url

logger = logging.getLogger(__name__)


def check_migrations() -> bool:
    config = open_config(silently_fail=True)

    if config is not None:
        for file in config["files"]:
            # migrate_add_project_url()
            if "project_url" not in file:
                return True


def migrate_add_project_url():
    logger.info("Migration in progress...")
    config = open_config()

    def on_exit():
        persist_config(config)

    atexit.register(on_exit)

    with tqdm_output(tqdm.tqdm(config["files"], miniters=5)) as progress_bar:
        for file in progress_bar:
            if "project_url" not in file:
                dl_url = file["downloads"][0]
                if "modrinth" in dl_url:
                    project_id = dl_url.split("/")[-4]
                    ret = get(f"https://api.modrinth.com/v2/project/{project_id}")
                    if ret is not None:
                        slug = ret["slug"]
                        file["project_url"] = f"https://modrinth.com/mod/{slug}"
                else:
                    file_id = dl_url.split("/")[-3].rjust(4, "0") + dl_url.split("/")[-2].rjust(3, "0")
                    mod_id = post(
                        "https://api.curse.tools/v1/cf/mods/files",
                        {"fileIds": [int(file_id)]},
                    )["data"][
                        0
                    ]["modId"]
                    project_url = cf_get_project_url(mod_id)
                    if project_url is not None:
                        file["project_url"] = project_url

    persist_config(config)
    atexit.unregister(on_exit)
    logger.info("Migration is done!")
