from modpacker.commands.add import add
from modpacker.packer_config import PackerConfig
from modpacker.services import modrinth


def test_simple_add_neoforge():
    packer_config = PackerConfig(
        {
            "formatVersion": 1,
            "game": "minecraft",
            "versionId": "0.0.1",
            "name": "Test",
            "summary": "",
            "dependencies": {"minecraft": "1.21.1", "neoforge": "21.1.218"},
            "files": [],
        }
    )

    provider = modrinth.ModrinthProvider(packer_config)
    ret = add(packer_config, provider, ["sodium"], False, True)
    assert len(ret) == 1
    check_version(ret[0], "sodium", {
        "client": "required",
        "server": "unsupported",
    })
    assert "sodium-neoforge" in ret[0]["downloads"][0]


def test_simple_add_fabric():
    packer_config = PackerConfig(
        {
            "formatVersion": 1,
            "game": "minecraft",
            "versionId": "0.0.1",
            "name": "Test",
            "summary": "",
            "dependencies": {"minecraft": "1.21.1", "fabric": "0.18.4"},
            "files": [],
        }
    )

    provider = modrinth.ModrinthProvider(packer_config)
    ret = add(packer_config, provider, ["sodium"], False, True)
    assert len(ret) == 1
    check_version(ret[0], "sodium", {
        "client": "required",
        "server": "unsupported",
    })
    assert "sodium-fabric" in ret[0]["downloads"][0]


def test_simple_with_deps_neoforge():
    packer_config = PackerConfig(
        {
            "formatVersion": 1,
            "game": "minecraft",
            "versionId": "0.0.1",
            "name": "Test",
            "summary": "",
            "dependencies": {"minecraft": "1.21.1", "neoforge": "21.1.218"},
            "files": [],
        }
    )

    provider = modrinth.ModrinthProvider(packer_config)
    ret = add(packer_config, provider, ["applied-mekanistics"], False, True)

    assert len(ret) == 4

    check_version(ret[0], "applied-mekanistics", {
        "client": "required",
        "server": "required",
    })
    check_version(ret[1], "ae2", {
        "client": "required",
        "server": "required",
    })
    check_version(ret[2], "guideme", {
        "client": "required",
        "server": "required",
    })
    check_version(ret[3], "mekanism", {
        "client": "required",
        "server": "required",
    })

def check_version(version, slug, env):
    assert version["slug"] == slug
    assert version["project_url"] == f"https://modrinth.com/mod/{slug}"
    assert version["env"] == env
    assert len(version["downloads"]) == 1
    assert "modrinth.com" in version["downloads"][0]
