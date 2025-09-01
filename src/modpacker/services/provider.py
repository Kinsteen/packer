import logging

logger = logging.getLogger(__name__)


class ModProvider:
    @staticmethod
    def search_slug(slug: str):
        pass

    @staticmethod
    def resolve_dependencies(mod_id: str, version_id: str, _current_list=None) -> list[dict]:
        pass

    @staticmethod
    def get_download_link(slug: str, version: dict):
        pass
