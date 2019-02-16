__all__ = ['Environment']
import os
from helpers.decorators import singleton


@singleton
class Environment(object):
    def __getattr__(self, item):
        return {k.lower(): v for k, v in os.environ.items()}.get(item)
