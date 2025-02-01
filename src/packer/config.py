import atexit
import json
import os
from typing import Callable


def on_exit():
    persist_cache()


atexit.register(on_exit)
cache = None


def open_config():
    with open("packer_config.json") as f:
        return json.loads(f.read())


def persist_config(config: dict):
    with open("packer_config.json", "w") as f:
        f.write(json.dumps(config, indent=4))


def load_cache():
    global cache
    # Cache should always be loaded quickly
    if not os.path.exists("packer_cache.json"):
        cache = {}
    with open("packer_cache.json", "r") as cache:
        try:
            cache = json.loads(cache.read())
        except Exception:
            with open("packer_cache.json", "w") as new_cache:
                new_cache.write("{}")


def order_dict(dictionary):
    return {k: order_dict(v) if isinstance(v, dict) else v for k, v in sorted(dictionary.items())}


def persist_cache() -> dict:
    global cache
    if cache is not None:
        with open("packer_cache.json", "w") as new_cache:
            new_cache.write(json.dumps(order_dict(cache), indent=4))


def set_cache(key, val):
    cache[key] = val


def get_from_cache(name: str, property: str, get: Callable):
    global cache
    try:
        return cache[name][property]
    except KeyError:
        if name not in cache:
            cache[name] = {}
        cache[name][property] = get()
