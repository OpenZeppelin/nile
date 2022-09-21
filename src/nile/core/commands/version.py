"""Command to print Nile version."""
from nile import __version__ as nile_version


def version():
    """Print Nile version."""
    print(nile_version)
