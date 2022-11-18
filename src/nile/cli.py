#!/usr/bin/env python
"""Nile CLI entry point."""
import logging
import os

import asyncclick as click

from nile.common import is_alias
from nile.core.account import Account, get_counterfactual_address
from nile.core.call_or_invoke import call_or_invoke as call_or_invoke_command
from nile.core.clean import clean as clean_command
from nile.core.compile import compile as compile_command
from nile.core.deploy import deploy as deploy_command
from nile.core.init import init as init_command
from nile.core.node import node as node_command
from nile.core.plugins import load_plugins
from nile.core.run import run as run_command
from nile.core.test import test as test_command
from nile.core.version import version as version_command
from nile.signer import Signer
from nile.utils import hex_address, normalize_number, shorten_address
from nile.utils.get_accounts import get_accounts as get_accounts_command
from nile.utils.get_accounts import (
    get_predeployed_accounts as get_predeployed_accounts_command,
)
from nile.utils.get_balance import get_balance as get_balance_command
from nile.utils.get_nonce import get_nonce as get_nonce_command
from nile.utils.status import status as status_command

logging.basicConfig(level=logging.DEBUG, format="%(message)s")
logging.getLogger("asyncio").setLevel(logging.WARNING)

NETWORKS = ("localhost", "integration", "goerli", "goerli2", "mainnet")


def network_option(f):
    """Configure NETWORK option for the cli."""
    return click.option(  # noqa: E731
        "--network",
        envvar="STARKNET_NETWORK",
        default="localhost",
        help=f"Select network, one of {NETWORKS}",
        callback=_validate_network,
    )(f)


def watch_option(f):
    """Handle track and debug options for the cli."""
    f = click.option("--track", "-t", "watch_mode", flag_value="track")(f)
    f = click.option("--debug", "-d", "watch_mode", flag_value="debug", default=True)(f)
    return f


def mainnet_token_option(f):
    """Configure TOKEN option for the cli."""
    return click.option(
        "--token",
        help="Used for deploying contracts in Alpha Mainnet.",
    )(f)


def _validate_network(_ctx, _param, value):
    """Normalize network values."""
    # check if value is known
    if value in NETWORKS:
        return value
    # normalize goerli
    if "testnet" == value:
        return "goerli"
    # normalize localhost
    if "127.0.0.1" == value:
        return "localhost"
    # raise if value is invalid
    raise click.BadParameter(f"'{value}'. Use one of {NETWORKS}")


@click.group()
def cli():
    """Nile CLI group."""
    pass


@cli.command()
def init():
    """Nile CLI group."""
    init_command()


@cli.command()
@click.argument("path", nargs=1)
@network_option
async def run(path, network):
    """Run Nile scripts with NileRuntimeEnvironment."""
    await run_command(path, network)


@cli.command()
@click.argument("signer", nargs=1)
@click.argument("contract_name", nargs=1)
@click.argument("params", nargs=-1)
@click.option("--max_fee", nargs=1)
@click.option("--salt", nargs=1, default=0)
@click.option("--unique", is_flag=True)
@click.option("--alias")
@click.option("--abi")
@click.option("--deployer_address")
@click.option(
    "--ignore_account",
    is_flag=True,
    help="Deploy without Account.",
)
@mainnet_token_option
@network_option
@watch_option
async def deploy(
    signer,
    contract_name,
    salt,
    params,
    max_fee,
    unique,
    alias,
    abi,
    deployer_address,
    ignore_account,
    token,
    network,
    watch_mode,
):
    """Deploy a StarkNet smart contract."""
    if not ignore_account:
        account = await Account(signer, network)
        await account.deploy_contract(
            contract_name,
            salt,
            unique,
            params,
            alias,
            deployer_address=deployer_address,
            max_fee=max_fee,
            abi=abi,
            watch_mode=watch_mode,
        )
    else:
        await deploy_command(
            contract_name,
            params,
            network,
            alias,
            abi=abi,
            mainnet_token=token,
            watch_mode=watch_mode,
        )


@cli.command()
@click.argument("signer", nargs=1)
@click.argument("contract_name", nargs=1)
@click.option("--max_fee", nargs=1)
@click.option("--alias")
@click.option("--overriding_path")
@network_option
@mainnet_token_option
@watch_option
async def declare(
    signer,
    contract_name,
    network,
    max_fee,
    watch_mode,
    alias,
    overriding_path,
    token,
):
    """Declare a StarkNet smart contract through an Account."""
    account = await Account(signer, network)
    await account.declare(
        contract_name,
        alias=alias,
        max_fee=max_fee,
        overriding_path=overriding_path,
        mainnet_token=token,
        watch_mode=watch_mode,
    )


@cli.command()
@click.argument("signer", nargs=1)
@click.option("--salt", nargs=1)
@click.option("--max_fee", nargs=1)
@network_option
@watch_option
async def setup(signer, network, salt, max_fee, watch_mode):
    """Set up an Account contract."""
    await Account(signer, network, salt, max_fee, watch_mode=watch_mode)


@cli.command()
@click.argument("signer", nargs=1)
@click.option("--salt", nargs=1, default=None)
def counterfactual_address(signer, salt):
    """Precompute the address of an Account contract."""
    _signer = Signer(normalize_number(os.environ[signer]))
    address = hex_address(
        get_counterfactual_address(salt, calldata=[_signer.public_key])
    )
    logging.info(address)


@cli.command()
@click.argument("signer", nargs=1)
@click.argument("address_or_alias", nargs=1)
@click.argument("method", nargs=1)
@click.argument("params", nargs=-1)
@click.option("--max_fee", nargs=1)
@click.option("--simulate", "query", flag_value="simulate")
@click.option("--estimate_fee", "query", flag_value="estimate_fee")
@network_option
@watch_option
async def send(
    signer,
    address_or_alias,
    method,
    params,
    network,
    max_fee,
    query,
    watch_mode,
):
    """Invoke a contract's method through an Account."""
    account = await Account(signer, network)
    print(
        "Calling {} on {} with params: {}".format(
            method, address_or_alias, [x for x in params]
        )
    )
    # address_or_alias is not normalized first here because
    # Account.send is part of Nile's public API and can accept hex addresses
    await account.send(
        address_or_alias,
        method,
        params,
        max_fee=max_fee,
        query_type=query,
        watch_mode=watch_mode,
    )


@cli.command()
@click.argument("address_or_alias", nargs=1)
@click.argument("method", nargs=1)
@click.argument("params", nargs=-1)
@network_option
async def call(address_or_alias, method, params, network):
    """Call functions of StarkNet smart contracts."""
    if not is_alias(address_or_alias):
        address_or_alias = normalize_number(address_or_alias)
    out = await call_or_invoke_command(
        address_or_alias, "call", method, params, network
    )
    logging.info(out)


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
@click.option("--directory")
@click.option("--cairo_path")
@click.option("--account_contract", is_flag="True")
@click.option("--disable-hint-validation", is_flag=True)
def compile(
    contracts, directory, cairo_path, account_contract, disable_hint_validation
):
    """
    Compile cairo contracts.

    $ compile.py
      Compiles all contracts in CONTRACTS_DIRECTORY

    $ compile.py contracts/MyContract.cairo
      Compiles MyContract.cairo

    $ compile.py contracts/foo.cairo contracts/bar.cairo
      Compiles foo.cairo and bar.cairo
    """
    compile_command(
        contracts, directory, cairo_path, account_contract, disable_hint_validation
    )


@cli.command()
def clean():
    """Remove default build directory."""
    clean_command()


@cli.command()
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=5050)
@click.option("--seed", type=int)
@click.option("--lite_mode", is_flag=True)
def node(host, port, seed, lite_mode):
    """Start StarkNet local network.

    $ nile node
      Start StarkNet local network at port 5050

    $ nile node --host HOST --port 5001
      Start StarkNet network on address HOST listening at port 5001

    $ nile node --seed SEED
      Start StarkNet local network with seed SEED

    $ nile node --lite_mode
      Start StarkNet network on lite-mode
    """
    node_command(host, port, seed, lite_mode)


@cli.command()
@click.version_option()
def version():
    """Print out toolchain version."""
    version_command()


@cli.command()
@click.argument("tx_hash", nargs=1)
@click.option("--contracts_file", nargs=1)
@network_option
async def debug(tx_hash, network, contracts_file):
    """
    Locate an error in a transaction using available contracts.

    Alias for `nile status --debug`.
    """
    await status_command(normalize_number(tx_hash), network, "debug", contracts_file)


@cli.command()
@click.argument("tx_hash", nargs=1)
@click.option("--contracts_file", nargs=1)
@network_option
@watch_option
async def status(tx_hash, network, watch_mode, contracts_file):
    """
    Get the status of a transaction.

    $ nile status transaction_hash
      Get the current status of a transaction.

    $ nile status --track transaction_hash
      Get (wait for) the final status of a transaction (REJECTED / ACCEPTED ON L2)

    $ nile status --debug transaction_hash
      Same as `status --track` then locate errors if rejected using local artifacts
    """
    await status_command(
        normalize_number(tx_hash),
        network,
        watch_mode=watch_mode,
        contracts_file=contracts_file,
    )


@cli.command()
@click.option("--predeployed/--registered", default=False)
@network_option
async def get_accounts(network, predeployed):
    """Retrieve and manage deployed accounts."""
    if not predeployed:
        await get_accounts_command(network)
    else:
        await get_predeployed_accounts_command(network)


@cli.command()
@click.argument("contract_address")
@network_option
async def get_balance(contract_address, network):
    """Retrieve the Ether balance for a given contract."""
    balance = await get_balance_command(
        normalize_number(contract_address), network=network
    )
    logging.info(f"🕵️  {shorten_address(contract_address)} balance is:")
    if balance < 10**6:
        logging.info(f"🪙  {balance} wei")
    elif balance < 10**15:
        logging.info(f"💰 {balance / 10 ** 9} gwei")
    else:
        logging.info(f"🤑 {balance / 10 ** 18} ether")


@cli.command()
@click.argument("contract_address")
@network_option
async def get_nonce(contract_address, network):
    """Retrieve the nonce for a contract."""
    await get_nonce_command(normalize_number(contract_address), network)


cli = load_plugins(cli)


if __name__ == "__main__":
    cli(_anyion_backend="asyncio")
