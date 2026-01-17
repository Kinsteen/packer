import json
import logging
import os
from collections.abc import Callable
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


class Cache:
    def __init__(self, cache_file="packer_cache.json", cache_folder="."):
        self._cache_file_path = os.path.join(os.path.realpath(cache_folder), cache_file)
        self._cache_folder_path = os.path.realpath(cache_folder)
        logger.debug("Loading cache from %s", self._cache_file_path)
        if not os.path.exists(self._cache_file_path):
            self._cache = {}
        else:
            with open(self._cache_file_path, "r") as cache:
                try:
                    self._cache = json.loads(cache.read())
                except Exception:
                    self._cache = {}

    def get_or(self, path: str, key: str, loader: Callable[[], str]):
        try:
            return self._cache[path][key]
        except KeyError:
            if path not in self._cache:
                self._cache[path] = {}
            self._cache[path][key] = loader()
            return self._cache[path][key]

    def set(self, path: str, key: str, value: str):
        self._cache[path][key] = value

    def persist(self):
        if self._cache is not None and len(self._cache.keys()) > 0:
            with open(self._cache_file_path, "w") as new_cache:
                new_cache.write(json.dumps(_order_dict(self._cache), indent=4))

    def read_or_download(self, path: str, url: str) -> bytes:
        cache_path = Path(os.path.join(self._cache_folder_path, path))
        if cache_path.exists():
            with open(cache_path, "rb") as f:
                return f.read()
        else:
            logger.info(f"Downloading {url}")
            remote = requests.get(url)
            if not cache_path.parent.exists():
                os.makedirs(cache_path.parent, exist_ok=True)
            with open(cache_path, "wb") as f:
                f.write(remote.content)
            return remote.content

def _order_dict(dictionary):
    return {
        k: _order_dict(v) if isinstance(v, dict) else v
        for k, v in sorted(dictionary.items())
    }
