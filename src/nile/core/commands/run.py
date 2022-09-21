"""Command to run Nile scripts."""
import logging
from importlib.machinery import SourceFileLoader

from nile.nre import NileRuntimeEnvironment


def run(path, network):
    """Run nile scripts passing on the NRE object."""
    logger = logging.getLogger()
    logger.disabled = True
    script = SourceFileLoader("script", path).load_module()
    nre = NileRuntimeEnvironment(network)
    script.run(nre)
