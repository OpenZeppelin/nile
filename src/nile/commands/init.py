"""Command to kickstart a Nile project."""
import os
import subprocess
import sys
from distutils.dir_util import copy_tree

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
    copy_tree(os.path.join(os.path.dirname(__file__), "../base_project"), ".")

    print("⛵️ Nile project ready! Try running:")
    print("")
    print("nile compile")
    print("")
