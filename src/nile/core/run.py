"""Command to clean artifacts from workspace."""
from importlib.machinery import SourceFileLoader

from nile.nre import NileRuntimeEnvironment


def run(path, network):
    """Run nile scripts passing on the NRE object."""
    script = SourceFileLoader("script", path).load_module()
    nre = NileRuntimeEnvironment(network)
    script.run(nre)
