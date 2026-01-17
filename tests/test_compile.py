import os
from modpacker import config
from modpacker.compile import compile
from modpacker.packer_config import PackerConfig


def test_simple_compile(tmp_path):
    config.load_cache()

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

    compile(packer_config, output_folder=tmp_path)

    assert len(os.listdir(tmp_path)) == 1
    assert os.listdir(tmp_path)[0] == "Test-0.0.1.mrpack"

def test_simple_compile_prism(tmp_path):
    # TODO create a real cache class/instance, and insert a fake cache (that write to tmp_path/cache)
    config.load_cache()

    packer_config = PackerConfig(
        {
            "formatVersion": 1,
            "game": "minecraft",
            "versionId": "0.0.1",
            "name": "Test",
            "summary": "",
            "dependencies": {"minecraft": "1.21.1", "neoforge": "21.1.218"},
            "unsup": {
                "version": "1.2.0-pre4",
                "source": "http://localhost:8000/packwiz/pack.toml",
            },
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

    output_path = os.path.join(tmp_path, "output")

    compile(packer_config, prism=True, output_folder=output_path)

    assert len(os.listdir(output_path)) == 1
    assert os.listdir(output_path)[0] == "Test-0.0.1-prism.zip"
