# Packer
[![PyPI - Version](https://img.shields.io/pypi/v/modpacker)](https://pypi.org/project/modpacker)

*The best Minecraft modpack creation tool you know*

## Usage
Install with:
```bash
pip install modpacker # stable release
pip install https://github.com/Kinsteen/packer/releases/download/main/modpacker-0.0.1-py3-none-any.whl # rolling release
```

Run with `packer`! (you have to have it in path, pip will complain if it's not anyway)

Running the help will show you what you can do with it (`packer --help` and `packer <subcommand> --help`)

### Creating a modpack
In an empty directory, create a `packer_config.json` file.
```json
{
    "formatVersion": 1,
    "game": "minecraft",
    "versionId": "0.0.1",
    "name": "Modpack name",
    "summary": "Modpack description",
    "dependencies": {
        "minecraft": "1.21.1",
        "neoforge": "21.1.130"
    },
    "files": []
}
```

You can now run `packer (curseforge/modrinth) add <slug>` to add mods!

Create a `overrides` folder to have arbitrary files included in the modpack (example: `/overrides/config/config.toml`)

Export the modpack to .mrpack format with `packer compile`, or export to packwiz format with `packer packwiz <packwiz export folder>`.

If you want to use Git to version your modpack, you should add a `.gitignore` with:
```
/.cache
/packer_cache.json
*.mrpack
```

## Development
Simply run:
```bash
pip install --edit ".[dev]"
```

You can run the formatters + linters:
```
./format+lint.sh

# OR

isort src
black src
ruff check src
```
