"""Command to install a specific version of Cairo."""
import logging
import subprocess
import sys


def install():
    """Install Cairo package with the given tag."""
    logging.info("🗄  Installing Cairo")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "cairo-lang", "starknet-devnet"]
    )
    logging.info("✨  Cairo successfully installed!")
