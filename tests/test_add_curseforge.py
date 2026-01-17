from modpacker.commands.add import add
from modpacker.packer_config import PackerConfig
from modpacker.services import curseforge


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

    provider = curseforge.CurseforgeProvider(packer_config)
    ret = add(packer_config, provider, ["sodium"], False, True)
    assert len(ret) == 1
    assert ret[0]["slug"] == "sodium"
    assert ret[0]["project_url"] == "https://www.curseforge.com/minecraft/mc-mods/sodium"
    assert ret[0]["env"] == {
        "client": "required",
        "server": "unsupported",
    }
    assert len(ret[0]["downloads"]) == 1
    assert "forgecdn.net" in ret[0]["downloads"][0]
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

    provider = curseforge.CurseforgeProvider(packer_config)
    ret = add(packer_config, provider, ["sodium"], False, True)
    assert len(ret) == 1
    assert ret[0]["slug"] == "sodium"
    assert ret[0]["project_url"] == "https://www.curseforge.com/minecraft/mc-mods/sodium"
    assert ret[0]["env"] == {
        "client": "required",
        "server": "unsupported",
    }
    assert len(ret[0]["downloads"]) == 1
    assert "forgecdn.net" in ret[0]["downloads"][0]
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

    provider = curseforge.CurseforgeProvider(packer_config)
    ret = add(packer_config, provider, ["applied-mekanistics"], False, True)

    assert len(ret) == 4
    assert ret[0]["slug"] == "applied-mekanistics"
    assert ret[0]["project_url"] == "https://www.curseforge.com/minecraft/mc-mods/applied-mekanistics"
    assert ret[0]["env"] == {
        "client": "required",
        "server": "required",
    }
    assert len(ret[0]["downloads"]) == 1
    assert "forgecdn.net" in ret[0]["downloads"][0]

    assert ret[1]["slug"] == "mekanism"
    assert ret[1]["project_url"] == "https://www.curseforge.com/minecraft/mc-mods/mekanism"
    assert ret[1]["env"] == {
        "client": "required",
        "server": "required",
    }
    assert len(ret[1]["downloads"]) == 1
    assert "forgecdn.net" in ret[1]["downloads"][0]

    assert ret[2]["slug"] == "applied-energistics-2"
    assert ret[2]["project_url"] == "https://www.curseforge.com/minecraft/mc-mods/applied-energistics-2"
    assert ret[2]["env"] == {
        "client": "required",
        "server": "required",
    }
    assert len(ret[2]["downloads"]) == 1
    assert "forgecdn.net" in ret[2]["downloads"][0]

    assert ret[3]["slug"] == "guideme"
    assert ret[3]["project_url"] == "https://www.curseforge.com/minecraft/mc-mods/guideme"
    assert ret[3]["env"] == {
        "client": "required",
        "server": "required",
    }
    assert len(ret[3]["downloads"]) == 1
    assert "forgecdn.net" in ret[3]["downloads"][0]
