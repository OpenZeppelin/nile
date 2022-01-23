#!/usr/bin/env python
"""Nile CLI entry point."""
import click

from nile.core.account import (
    account_raw_execute,
    account_send,
    account_setup,
)
from nile.core.call_or_invoke import call_or_invoke as casll_or_invoke_command
from nile.core.clean import clean as clean_command
from nile.core.compile import compile as compile_command
from nile.core.deploy import deploy as deploy_comand
from nile.core.init import init as init_command
from nile.core.install import install as install_command
from nile.core.node import node as node_command
from nile.core.test import test as test_command
from nile.core.version import version as version_command


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
@click.argument("arguments", nargs=-1)
@click.option("--network", default="localhost")
@click.option("--alias")
def deploy(artifact, arguments, network, alias):
    """Deploy StarkNet smart contract."""
    deploy_comand(artifact, arguments, network, alias)


@cli.command()
@click.argument("signer", nargs=1)
@click.argument("contract_name", nargs=1)
@click.argument("method", nargs=1)
@click.argument("params", nargs=-1)
@click.option("--network", default="localhost")
def send(signer, contract_name, method, params, network):
    """Invoke a contract's method through an Account. Same usage as nile invoke."""
    account_send(signer, contract_name, method, params, network)


@cli.command(name="raw-execute")
@click.argument("signer", nargs=1)
@click.argument("params", nargs=-1)
@click.option("--network", default="localhost")
def raw_execute(signer, params, network):
    """Invoke a contract through an Account."""
    account_raw_execute(signer, params, network)


@cli.command()
@click.argument("signer", nargs=1)
@click.option("--network", default="localhost")
def setup(signer, network):
    """Do setup an Account contract."""
    account_setup(signer, network)


@cli.command()
@click.argument("contract_name", nargs=1)
@click.argument("method", nargs=1)
@click.argument("params", nargs=-1)
@click.option("--network", default="localhost")
def invoke(contract_name, method, params, network):
    """Invoke functions of StarkNet smart contracts."""
    casll_or_invoke_command(contract_name, "invoke", method, params, network)


@cli.command()
@click.argument("contract_name", nargs=1)
@click.argument("method", nargs=1)
@click.argument("params", nargs=-1)
@click.option("--network", default="localhost")
def call(contract_name, method, params, network):
    """Call functions of StarkNet smart contracts."""
    casll_or_invoke_command(contract_name, "call", method, params, network)


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
    clean_command()


@cli.command()
@click.option("--host", default="localhost")
@click.option("--port", default=5000)
def node(host, port):
    """Start StarkNet local network.

    $ nile node
      Start StarkNet local network at port 5000

    $ nile node --host HOST --port 5001
      Start StarkNet network on address HOST listening at port 5001
    """
    node_command(host, port)


@cli.command()
@click.version_option()
def version():
    """Print out toolchain version."""
    version_command()


if __name__ == "__main__":
    cli()
