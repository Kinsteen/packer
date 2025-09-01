import logging

logger = logging.getLogger(__name__)


class ModProvider:
    def get_mod(self, slug):
        pass

    def pick_mod_version(self, mod, minecraft_version, mod_loader, latest=False):
        pass

    def resolve_dependencies(self, mod_id, version_id, latest=False, _current_list=None) -> list[dict]:
        pass

    @staticmethod
    def get_download_link(slug: str, version: dict):
        pass
