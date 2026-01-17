import json
import os
from typing import Callable

from jsonschema import validate

packer_config_schema = {
    "type": "object",
    "properties": {
        "formatVersion": {
            "type": "integer",
            "minimum": 1
        },
        "game": {
            "type": "string",
        },
        "versionId": {
            "type": "string",
        },
        "name": {
            "type": "string",
        },
        "summary": {
            "type": "string",
        },
        "dependencies": {
            "type": "object",
            "properties": {
                "minecraft": {
                    "type": "string"
                }
            },
            "required": ["minecraft"]
        },
        "unsup": {
            "type": "object",
            "properties": {
                "version": {
                    "type": "string"
                },
                "source": {
                    "type": "string"
                },
                "signature": {
                    "type": "string"
                }
            },
            "required": [
                "version",
                "source",
            ]
        },
        "files": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "enum": ["MOD", "RESOURCE_PACK", "SHADER"]
                    },
                    "slug": {
                        "type": "string"
                    },
                    "version_id": {
                        "type": "string",
                    },
                    "project_url": {
                        "type": "string"
                    },
                    "downloads": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    "env": {
                        "type": "object",
                        "properties": {
                            "client": {
                                "enum": ["required", "unsupported"]
                            },
                            "server": {
                                "enum": ["required", "unsupported"]
                            }
                        },
                        "required": [
                            "client",
                            "server"
                        ]
                    }
                },
                "required": [
                    "downloads",
                    "env"
                ]
            }
        }
    },
    "required": [
        "formatVersion",
        "game",
        "versionId",
        "name",
        "dependencies",
        "files"
    ]
}

def open_config():
    with open("packer_config.json") as f:
        data = json.loads(f.read())

    validate(instance=data, schema=packer_config_schema)

    # Validity checks
    if data["formatVersion"] != 1:
        raise Exception("packer_config.json only support 'formatVersion': 1.")
    if data["game"] != "minecraft":
        raise Exception("packer_config.json only support 'game': 'minecraft'.")

    seen_mods = set()
    for mod in data["files"]:
        if mod["slug"] in seen_mods:
            raise Exception(f"There is a duplicate mod in 'packer_config.json': {mod['slug']}. Delete one or the other!")
        seen_mods.add(mod["slug"])

    return data


def persist_config(config: dict):
    with open("packer_config.json", "w") as f:
        f.write(json.dumps(config, indent=4))


def load_cache():
    global cache
    if not os.path.exists("packer_cache.json"):
        cache = {}
    else:
        with open("packer_cache.json", "r") as cache:
            try:
                cache = json.loads(cache.read())
            except Exception:
                cache = {}

def order_file_keys(config):
    ordered_keys = ["type", "slug", "project_url", "version_id", "env", "downloads"]
    def key_func(key):
        return ordered_keys.index(key[0])

    return {
        #k: [sorted(mod, key=key_func) for mod in v] if k == "files" else v
        k: [{x: y for x, y in sorted(mod.items(), key=key_func)} for mod in v] if k == "files" else v
        for k, v in config.items()
    }

def order_top_keys(config):
    ordered_keys = ["formatVersion", "game", "name", "versionId", "summary", "dependencies", "unsup", "files"]
    def key_func(key):
        return ordered_keys.index(key[0])

    return {
        k: v
        for k, v in sorted(config.items(), key=key_func)
    }


def order_dict(dictionary):
    return {
        k: order_dict(v) if isinstance(v, dict) else v
        for k, v in sorted(dictionary.items())
    }


def set_cache(key, val):
    global cache
    cache[key] = val


def get_from_cache(name: str, property: str, get: Callable):
    global cache
    try:
        return cache[name][property]
    except KeyError:
        if name not in cache:
            cache[name] = {}
        cache[name][property] = get()
        return cache[name][property]
