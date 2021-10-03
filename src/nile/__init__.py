"""StarkNet/Cairo development toolbelt."""
import sys

if sys.version_info == (3, 7):
    from importlib.metadata import PackageNotFoundError, version
else:
    from importlib_metadata import PackageNotFoundError, version

try:
    __version__ = version("nile")
except PackageNotFoundError:
    # package is not installed
    __version__ = None
