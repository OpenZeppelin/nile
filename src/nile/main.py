#!/usr/bin/env python
"""Nile CLI entry point."""
import os
import shutil

import click

from nile.commands.call import call_or_invoke_command
from nile.commands.compile import compile_command
from nile.commands.deploy import deploy_command
from nile.commands.init import init_command
from nile.commands.install import install_command
from nile.commands.node import node_command
from nile.commands.test import test_command
from nile.commands.version import version_command
from nile.common import BUILD_DIRECTORY, DEPLOYMENTS_FILENAME


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
@click.argument("artifact", nargs=1)
@click.option("--network", default="localhost")
@click.option("--alias")
def deploy(artifact, network, alias):
    """Deploy StarkNet smart contract."""
    deploy_command(artifact, network, alias)


@cli.command()
@click.argument("contract_name", nargs=1)
@click.argument("method", nargs=1)
@click.argument("params", nargs=-1)
@click.option("--network", default="localhost")
def invoke(contract_name, method, params, network):
    """Invoke functions of StarkNet smart contracts."""
    call_or_invoke_command(contract_name, "invoke", method, params, network)


@cli.command()
@click.argument("contract_name", nargs=1)
@click.argument("method", nargs=1)
@click.argument("params", nargs=-1)
@click.option("--network", default="localhost")
def call(contract_name, method, params, network):
    """Call functions of StarkNet smart contracts."""
    call_or_invoke_command(contract_name, "call", method, params, network)


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
    local_deployments_filename = f"localhost.{DEPLOYMENTS_FILENAME}"

    if os.path.exists(local_deployments_filename):
        print(f"🚮 Deleting {local_deployments_filename}")
        os.remove(local_deployments_filename)

    if os.path.exists(BUILD_DIRECTORY):
        print(f"🚮 Deleting {BUILD_DIRECTORY} directory")
        shutil.rmtree(BUILD_DIRECTORY)

    print("✨ Workspace clean, keep going!")


@cli.command()
def node():
    """Start StarkNet local network."""
    node_command()


@cli.command()
@click.version_option()
def version():
    """Print out toolchain version."""
    version_command()


if __name__ == "__main__":
    cli()
