#!/usr/bin/env python
"""Nile CLI entry point."""
import shutil

import click

from nile.commands.compile import compile_command
from nile.commands.install import install_command
from nile.commands.test import test_command
from nile.common import BUILD_DIRECTORY


@click.group()
def cli():
    """Nile CLI group."""
    pass


@cli.command()
@click.argument("tag")
def install(tag):
    """Install TAG version of Cairo."""
    install_command(tag)


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
def compile(contracts):
    """
    Compile cairo contracts.

    $ compile.py
      Compiles all contracts in CONTRACTS_DIRECTORY

    $ compile.py contracts/MyContract.cairo
      Compiles MyContract.cairo

    $ compile.py contracts/foo.cairo contracts/bar.cairo
      Compiles foo.cairo and bar.cairo
    """
    compile_command(contracts)


@cli.command()
def clean():
    """Remove default build directory."""
    shutil.rmtree(BUILD_DIRECTORY)


if __name__ == "__main__":
    cli()
