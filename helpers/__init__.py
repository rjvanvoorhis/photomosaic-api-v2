__all__ = ['file_transfers', 'image_server', 'page_builder', 'Environment', 'singleton']
import os
from helpers.decorators import singleton


class Environment(object):
    def __getattr__(self, item):
        return {k.lower(): v for k, v in os.environ.items()}.get(item)
