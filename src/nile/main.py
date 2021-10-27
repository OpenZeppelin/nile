#!/usr/bin/env python
"""Nile CLI entry point."""
import shutil

import click

from nile.commands.compile import (compile_command, CompilationOptions)
from nile.commands.init import init_command
from nile.commands.install import install_command
from nile.commands.test import test_command
from nile.commands.version import version_command
from nile.common import BUILD_DIRECTORY


@click.group()
def cli():
    """Nile CLI group."""
    pass


@cli.command()
def init():
    """Nile CLI group."""
    init_command()


@cli.command()
def install():
    """Install Cairo."""
    install_command()


@cli.command()
@click.argument("contracts", nargs=-1)
def test(contracts):
    """
    Run cairo test contracts.

    $ nile test
      Compiles all test contracts in CONTRACTS_DIRECTORY

    $ nile test contracts/MyContract.test.cairo
      Runs tests in MyContract.test.cairo

    $ nile test contracts/foo.test.cairo contracts/bar.test.cairo
      Runs tests in foo.test.cairo and bar.test.cairo
    """
    test_command(contracts)


@cli.command()
@click.argument("contracts", nargs=-1)
@click.option('--disable_hint_validation', is_flag=True, default=False)
def compile(contracts, disable_hint_validation):
    """
    Compile cairo contracts.

    $ compile.py
      Compiles all contracts in CONTRACTS_DIRECTORY

    $ compile.py contracts/MyContract.cairo
      Compiles MyContract.cairo

    $ compile.py contracts/foo.cairo contracts/bar.cairo
      Compiles foo.cairo and bar.cairo

    $ compile.py contracts/MyContract.cairo --disable_hint_validation
      Compiles MyContract.cairo without hints validation
    """

    opt: CompilationOptions = {
      "disable_hint_validation": True if disable_hint_validation else False
    }

    compile_command(contracts, opt)


@cli.command()
def clean():
    """Remove default build directory."""
    shutil.rmtree(BUILD_DIRECTORY)


@cli.command()
@click.version_option()
def version():
    """Print out toolchain version."""
    version_command()
    pass


if __name__ == "__main__":
    cli()
