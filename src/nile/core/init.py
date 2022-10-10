"""Command to kickstart a Nile project."""
import logging
from distutils.dir_util import copy_tree
from pathlib import Path


def init():
    """Kickstart a new Nile project."""
    # create project directories
    logging.info("🗄  Creating project directory tree")

    copy_tree(Path(__file__).parent.parent / "base_project", ".")

    with open("accounts.json", "w") as file:
        file.write("{}")

    logging.info("⛵️ Nile project ready! Try running:")
    logging.info("")
    logging.info("nile compile")
    logging.info("")
