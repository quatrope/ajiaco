import importlib

from .app import AjcApplication

__all__ = ["AjcApplication"]


VERSION = importlib.metadata.version("ajiaco")
