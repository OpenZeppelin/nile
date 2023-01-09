#!/usr/bin/env python
"""Nile CLI entry point."""

import logging
import os
from functools import update_wrapper

import asyncclick as click

from nile.common import is_alias
from nile.core.call_or_invoke import call_or_invoke as call_or_invoke_command
from nile.core.clean import clean as clean_command
from nile.core.compile import compile as compile_command
from nile.core.init import init as init_command
from nile.core.node import node as node_command
from nile.core.plugins import load_plugins
from nile.core.run import run as run_command
from nile.core.test import test as test_command
from nile.core.types.account import get_counterfactual_address, try_get_account
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


def enable_stack_trace(f):
    """Enable stack trace swapping for commands."""

    @click.pass_context
    async def new_func(ctx, *args, **kwargs):
        if ctx.obj["STACK_TRACE"]:
            return await ctx.invoke(f, ctx.obj, *args, **kwargs)
        else:
            try:
                return await ctx.invoke(f, ctx.obj, *args, **kwargs)
            except Exception as e:
                logging.error(
                    "The following exception occured while "
                    f"trying to execute the command:\n\n{repr(e)}\n\n"
                    "Try `nile --stack_trace [COMMAND]` for the full stack trace."
                )

    return update_wrapper(new_func, f)


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


def query_option(f):
    """Handle simulate and estimate_fee options for the cli."""
    f = click.option("--simulate", "query", flag_value="simulate")(f)
    f = click.option("--estimate_fee", "query", flag_value="estimate_fee")(f)
    return f


async def run_transaction(tx, query_flag, watch_mode):
    """Execute or simulate a transaction."""
    if query_flag == "estimate_fee":
        await tx.estimate_fee()
    elif query_flag == "simulate":
        await tx.simulate()
    else:
        await tx.execute(watch_mode=watch_mode)


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
@click.option("--stack_trace/--no_stack_trace", default=False)
@click.pass_context
def cli(ctx, stack_trace):
    """Nile CLI group."""
    # ensure that ctx.obj exists and is a dict
    ctx.ensure_object(dict)

    ctx.obj["STACK_TRACE"] = stack_trace


@cli.command()
@enable_stack_trace
def init(ctx):
    """Nile CLI group."""
    init_command()


@cli.command()
@click.argument("path", nargs=1)
@network_option
@enable_stack_trace
async def run(ctx, path, network):
    """Run Nile scripts with NileRuntimeEnvironment."""
    await run_command(path, network)


@cli.command()
@click.argument("signer", nargs=1)
@click.argument("contract_name", nargs=1)
@click.argument("params", nargs=-1)
@click.option("--max_fee", type=int, nargs=1)
@click.option("--salt", type=int, nargs=1, default=0)
@click.option("--unique", is_flag=True)
@click.option("--alias")
@click.option("--abi")
@click.option("--deployer_address")
@network_option
@query_option
@watch_option
@enable_stack_trace
async def deploy(
    ctx,
    signer,
    contract_name,
    salt,
    params,
    max_fee,
    unique,
    alias,
    abi,
    deployer_address,
    network,
    query,
    watch_mode,
):
    """Deploy a StarkNet smart contract."""
    account = await try_get_account(signer, network, watch_mode="track")
    if account is not None:
        transaction = await account.deploy_contract(
            contract_name,
            salt,
            unique,
            params,
            deployer_address=deployer_address,
            alias=alias,
            max_fee=max_fee,
            abi=abi,
        )

        await run_transaction(tx=transaction, query_flag=query, watch_mode=watch_mode)


@cli.command()
@click.argument("signer", nargs=1)
@click.argument("contract_name", nargs=1)
@click.option("--max_fee", type=int, nargs=1)
@click.option("--alias")
@click.option("--overriding_path")
@click.option("--nile_account", is_flag=True)
@network_option
@query_option
@watch_option
@enable_stack_trace
async def declare(
    ctx,
    signer,
    contract_name,
    network,
    max_fee,
    alias,
    overriding_path,
    query,
    nile_account,
    watch_mode,
):
    """Declare a StarkNet smart contract through an Account."""
    account = await try_get_account(signer, network, watch_mode="track")
    if account is not None:
        transaction = await account.declare(
            contract_name,
            max_fee=max_fee,
            alias=alias,
            overriding_path=overriding_path,
            nile_account=nile_account,
        )

        await run_transaction(tx=transaction, query_flag=query, watch_mode=watch_mode)


@cli.command()
@click.argument("signer", nargs=1)
@click.option("--salt", type=int, nargs=1)
@click.option("--max_fee", type=int, nargs=1)
@network_option
@query_option
@watch_option
@enable_stack_trace
async def setup(ctx, signer, network, salt, max_fee, query, watch_mode):
    """Set up an Account contract."""
    account = await try_get_account(signer, network, auto_deploy=False)
    if account is not None:
        transaction = await account.deploy(salt, max_fee)

        await run_transaction(tx=transaction, query_flag=query, watch_mode=watch_mode)


@cli.command()
@click.argument("signer", nargs=1)
@click.option("--salt", type=int, nargs=1)
@enable_stack_trace
def counterfactual_address(ctx, signer, salt):
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
@click.option("--max_fee", type=int, nargs=1)
@network_option
@query_option
@watch_option
@enable_stack_trace
async def send(
    ctx,
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
    account = await try_get_account(signer, network, watch_mode="track")
    if account is not None:
        print(
            "Calling {} on {} with params: {}".format(
                method, address_or_alias, [x for x in params]
            )
        )

        transaction = await account.send(
            address_or_alias,
            method,
            params,
            max_fee=max_fee,
        )

        await run_transaction(tx=transaction, query_flag=query, watch_mode=watch_mode)


@cli.command()
@click.argument("address_or_alias", nargs=1)
@click.argument("method", nargs=1)
@click.argument("params", nargs=-1)
@network_option
@enable_stack_trace
async def call(ctx, address_or_alias, method, params, network):
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
@enable_stack_trace
def compile(
    ctx, contracts, directory, cairo_path, account_contract, disable_hint_validation
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
@enable_stack_trace
def clean(ctx):
    """Remove default build directory."""
    clean_command()


@cli.command()
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=5050)
@click.option("--seed", type=int)
@click.option("--lite_mode", is_flag=True)
@enable_stack_trace
def node(ctx, host, port, seed, lite_mode):
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
@enable_stack_trace
def version(ctx):
    """Print out toolchain version."""
    version_command()


@cli.command()
@click.argument("tx_hash", nargs=1)
@click.option("--contracts_file", nargs=1)
@network_option
@enable_stack_trace
async def debug(ctx, tx_hash, network, contracts_file):
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
@enable_stack_trace
async def status(ctx, tx_hash, network, watch_mode, contracts_file):
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
@enable_stack_trace
async def get_accounts(ctx, network, predeployed):
    """Retrieve and manage deployed accounts."""
    if not predeployed:
        await get_accounts_command(network)
    else:
        await get_predeployed_accounts_command(network)


@cli.command()
@click.argument("contract_address")
@network_option
@enable_stack_trace
async def get_balance(ctx, contract_address, network):
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
@enable_stack_trace
async def get_nonce(ctx, contract_address, network):
    """Retrieve the nonce for a contract."""
    await get_nonce_command(normalize_number(contract_address), network)


cli = load_plugins(cli)


if __name__ == "__main__":
    cli(_anyion_backend="asyncio")
