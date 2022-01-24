"""Command to kickstart a Nile project."""
import logging
import subprocess
import sys
from distutils.dir_util import copy_tree
from pathlib import Path

from nile.core.install import install


def init():
    """Kickstart a new Nile project."""
    # install cairo dependencies
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "ecdsa", "fastecdsa", "sympy"]
    )

    # install cairo within env
    install()

    # install testing dependencies
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"]
    )
    logging.info("")
    logging.info("✅ Dependencies successfully installed")

    # create project directories
    logging.info("🗄  Creating project directory tree")

    copy_tree(Path(__file__).parent.parent / "base_project", ".")

    with open("accounts.json", "w") as file:
        file.write("{}")

    logging.info("⛵️ Nile project ready! Try running:")
    logging.info("")
    logging.info("nile compile")
    logging.info("")
