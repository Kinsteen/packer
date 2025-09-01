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
