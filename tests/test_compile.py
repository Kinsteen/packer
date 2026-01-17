import os

from modpacker.cache import Cache
from modpacker.compile import compile
from modpacker.packer_config import PackerConfig


def test_simple_compile(tmp_path):
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
    cache = Cache(cache_folder=os.path.join(tmp_path, ".cache"))

    output_path = os.path.join(tmp_path, "output")
    compile(packer_config, cache, output_folder=output_path)

    assert len(os.listdir(output_path)) == 1
    assert os.listdir(output_path)[0] == "Test-0.0.1.mrpack"

def test_simple_compile_prism(tmp_path):
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
    cache = Cache(cache_folder=os.path.join(tmp_path, ".cache"))

    output_path = os.path.join(tmp_path, "output")

    compile(packer_config, cache, prism=True, output_folder=output_path)

    assert len(os.listdir(output_path)) == 1
    assert os.listdir(output_path)[0] == "Test-0.0.1-prism.zip"
