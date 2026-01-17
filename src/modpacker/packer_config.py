

import requests

from modpacker.config import persist_config


class PackerConfig:
    def __init__(self, data: dict):
        self.data = data

    def __getitem__(self, item):
        return self.data[item]

    @property
    def mod_loader(self):
        if "neoforge" in self.data["dependencies"]:
            return "neoforge"
        elif "fabric" in self.data["dependencies"]:
            return "fabric"
        elif "forge" in self.data["dependencies"]:
            return "forge"

    @property
    def minecraft_version(self):
        return self.data["dependencies"]["minecraft"]

    def has_unsup(self):
        return "unsup" in self.data

    def get_recommended_lwjgl(self):
        r = requests.get("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json").json()
        for version in r["versions"]:
            if version["id"] == self.minecraft_version:
                version_meta = requests.get(version["url"]).json()
                for lib in version_meta["libraries"]:
                    if "org.lwjgl:lwjgl-glfw" in lib["name"]:
                        return lib["name"].split(":")[2]

    def persist(self):
        persist_config(self.data)
