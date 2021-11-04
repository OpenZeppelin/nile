"""Command to kickstart a Nile project."""
import subprocess
import sys
from distutils.dir_util import copy_tree
from pathlib import Path

from nile.commands.install import install_command


def init_command():
    """Kickstart a new Nile project."""
    # install cairo dependencies
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "ecdsa", "fastecdsa", "sympy"]
    )

    # install cairo within env
    install_command()

    # install testing dependencies
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"]
    )
    print("")
    print("✅ Dependencies successfully installed")

    # create project directories
    print("🗄  Creating project directory tree")

    copy_tree(Path(__file__).parent.parent / "base_project", ".")

    print("⛵️ Nile project ready! Try running:")
    print("")
    print("nile compile")
    print("")
