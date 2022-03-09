"""Command to run Nile scripts."""
import logging
import subprocess
from importlib.machinery import SourceFileLoader

from nile.nre import NileRuntimeEnvironment


def run(path, network, method):
    """Run nile scripts passing on the NRE object."""
    if method == "cairo":
        return _run_cairo(path)

    logger = logging.getLogger()
    logger.disabled = True
    script = SourceFileLoader("script", path).load_module()
    nre = NileRuntimeEnvironment(network)
    script.run(nre)


def _run_cairo(path):
    logging.info(f"🚀 Running Cairo program {path}")

    cmd = f"""
    cairo-run \
        --program={path} \
        --print_output --layout=small
    """ 

    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    out, err = process.communicate()
    logging.info(out.decode("UTF-8"))
    return process.returncode
