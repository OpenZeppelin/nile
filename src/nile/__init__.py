"""StarkNet/Cairo development toolbelt."""

try:
    from importlib import metadata as importlib_metadata
except ImportError:
    import importlib_metadata

try:
    __version__ = importlib_metadata.version("juli-nile")
except importlib_metadata.PackageNotFoundError:
    __version__ = None
