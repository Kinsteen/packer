import atexit
import logging

from packer.config import open_config, persist_config
from packer.api import get, post
from packer.curseforge import classid_to_cat

logger = logging.getLogger(__name__)

def check_migrations() -> bool:
    config = open_config()
    should_migrate = False

    # migrate_add_project_url()
    for file in config['files']:
        if "project_url" not in file:
            return True

def migrate_add_project_url():
    print("Migration in progress...")
    config = open_config()

    def on_exit():
        persist_config(config)

    atexit.register(on_exit)

    nb_files = len(config["files"])
    print("") # Empty line so it's removed by the in-place logger
    for idx, file in enumerate(config["files"]):
        if "project_url" not in file:
            dl_url = file['downloads'][0]
            if 'modrinth' in dl_url:
                project_id = dl_url.split('/')[-4]
                slug = get(f"https://api.modrinth.com/v2/project/{project_id}")['slug']
                file["project_url"] = f"https://modrinth.com/mod/{slug}"
            else:
                file_id = dl_url.split('/')[-3].rjust(4, "0") + dl_url.split('/')[-2].rjust(3, "0")
                mod_id = post('https://api.curse.tools/v1/cf/mods/files', {"fileIds": [int(file_id)]})['data'][0]['modId']
                mod = get(f"https://api.curse.tools/v1/cf/mods/{mod_id}")['data']
                try:
                    file["project_url"] = f"https://www.curseforge.com/minecraft/{classid_to_cat(mod['classId'])}/{mod['slug']}"
                except Exception:
                    print(dl_url)
                    print(mod['classId'])
                    print(mod['slug'])
                    print(mod['slug'])
                    print(mod['slug'])
        print(f"\033[A\033[KProgress: {idx+1}/{nb_files}")

    persist_config(config)
    atexit.unregister(on_exit)
    print("Migration is done!")
