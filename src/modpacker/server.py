import logging
import os
import shutil
import subprocess

import questionary
import requests
import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from modpacker.compile import read_or_download, unsup_ini_content
from modpacker.config import open_config

logger = logging.getLogger(__name__)


def export(output_folder):
    packer_config = open_config()
    output_folder = os.path.realpath(output_folder)
    if os.path.exists(output_folder):
        answer = questionary.confirm(f"This will delete {os.path.realpath(output_folder)}! Do you want to continue?").ask()
        if not answer:
            return
        shutil.rmtree(output_folder)
    os.makedirs(output_folder)

    if os.path.exists("overrides"):
        logger.info("Copying overrides...")
        for root, _, files in os.walk("overrides"):
            for file in files:
                path = os.path.join(root, file)
                destination = os.path.relpath(path, "overrides/")
                os.makedirs(os.path.dirname(os.path.join(output_folder, destination)), exist_ok=True)
                shutil.copy(os.path.join(root, file), os.path.join(output_folder, destination))

    logger.info("Copying mods...")
    with logging_redirect_tqdm():
        for file in tqdm.tqdm(packer_config["files"]):
            if "type" not in file or file["type"] == "MOD":
                if "env" in file and file["env"]["server"] == "required":
                    name = file["downloads"][0].split("/")[-1]
                    path = "mods/" + name
                    os.makedirs(os.path.dirname(os.path.join(output_folder, path)), exist_ok=True)
                    url = file["downloads"][0]
                    data = read_or_download(path, url)
                    with open(os.path.join(output_folder, path), "wb") as f:
                        f.write(data)

    if "dependencies" in packer_config and "neoforge" in packer_config["dependencies"]:
        logger.info("Neoforge detected. Downloading installer...")
        neoforge_installer = f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{packer_config['dependencies']['neoforge']}/neoforge-{packer_config['dependencies']['neoforge']}-installer.jar"
        installer_data = requests.get(neoforge_installer)
        with open(os.path.join(output_folder, "neo-installer.jar"), "wb") as f:
            f.write(installer_data.content)
        logger.info(f"Downloaded Neoforge installer in {os.path.join(output_folder, 'neo-installer.jar')}.")

        answer = questionary.confirm("Run server installer?").ask()
        if answer:
            installer_process = subprocess.Popen(["java", "-jar", os.path.join(output_folder, "neo-installer.jar"), "--install-server"], cwd=output_folder)
            code = installer_process.wait()
            if code == 0:
                answer = questionary.confirm("Delete Neoforge installer?").ask()
                if answer:
                    os.remove(os.path.join(output_folder, "neo-installer.jar"))
            else:
                logger.error("Neoforge installer encountered an error.")


    if "unsup" in packer_config:
        logger.info("Downloading unsup.jar and creating unsup.ini...")
        latest_release = requests.get(f"https://git.sleeping.town/api/v1/repos/unascribed/unsup/releases/tags/v{packer_config['unsup']['version']}").json()
        for asset in latest_release['assets']:
            if asset['name'].endswith('.jar'):
                unsup_jar = requests.get(asset['browser_download_url'])
                with open(os.path.join(output_folder, 'unsup.jar'), "wb") as f:
                    f.write(unsup_jar.content)

        with open(os.path.join(output_folder, 'unsup.ini'), "w") as f:
            f.write(unsup_ini_content(packer_config["unsup"]))
        
        if os.path.exists(os.path.join(output_folder, 'user_jvm_args.txt')):
            with open(os.path.join(output_folder, 'user_jvm_args.txt'), 'a') as f:
                f.write("\n-javaagent:unsup.jar")
            logger.info("Added `-javaagent:unsup.jar` to user_jvm_args.txt, you can start the server normally!")    
        else:
            logger.info("You should add `-javaagent:unsup.jar` to the server start command.")
