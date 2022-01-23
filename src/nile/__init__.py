"""StarkNet/Cairo development toolbelt."""

from nile.core.account import (
    account_raw_execute,
    account_send,
    account_setup,
)
from nile.core.call_or_invoke import call_or_invoke
from nile.core.compile import compile
from nile.core.deploy import deploy

try:
    from importlib import metadata as importlib_metadata
except ImportError:
    import importlib_metadata

try:
    __version__ = importlib_metadata.version("cairo-nile")
except importlib_metadata.PackageNotFoundError:
    __version__ = None
