import os

from modpacker.packer_config import PackerConfig
from modpacker.server import export


def test_simple_export(tmp_path):
    packer_config = PackerConfig(
        {
            "formatVersion": 1,
            "game": "minecraft",
            "versionId": "0.0.1",
            "name": "Test",
            "summary": "",
            "dependencies": {"minecraft": "1.21.1", "neoforge": "21.1.218"},
            "files": [
                {
                    "slug": "mekanism",
                    "version_id": "D32JUF51",
                    "project_url": "https://modrinth.com/mod/mekanism",
                    "downloads": ["https://cdn.modrinth.com/data/Ce6I4WUE/versions/D32JUF51/Mekanism-1.21.1-10.7.17.83.jar"],
                    "env": {"client": "required", "server": "required"},
                }
            ],
        }
    )

    export(packer_config, tmp_path, unattended=True)

    assert len(os.listdir(tmp_path / "mods")) == 1
    assert os.listdir(tmp_path / "mods")[0].startswith("Mekanism-1.21.1-")
    assert os.listdir(tmp_path / "mods")[0].endswith(".jar")
