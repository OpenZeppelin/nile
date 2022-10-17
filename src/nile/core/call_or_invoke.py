"""Command to call or invoke StarkNet smart contracts."""
import argparse
import logging

from nile import deployments
from nile.common import get_gateway_url, get_feeder_url, prepare_params, capture_stdout
from nile.core import account
from nile.utils import hex_address
from starkware.starknet.cli.starknet_cli import call, invoke, AbiFormatError

async def call_or_invoke(
    contract, type, method, params, network, signature=None, max_fee=None
):
    """Call or invoke functions of StarkNet smart contracts."""
    if isinstance(contract, account.Account):
        address = contract.address
        abi = contract.abi_path
    else:
        address, abi = next(deployments.load(contract, network))

    address = hex_address(address)
    command = [
        "--address",
        address,
        "--abi",
        abi,
        "--function",
        method,
    ]

    params = prepare_params(params)

    if len(params) > 0:
        command.append("--inputs")
        command.extend(params)

    if signature is not None:
        command.append("--signature")
        command.extend(signature)

    if max_fee is not None:
        command.append("--max_fee")
        command.append(max_fee)

    if type == "call":
        try:
            return await _call_command(command, network)
        except AbiFormatError as err:
            logging.error(err)

    elif type == "invoke":
        try:
            return await _invoke_command(command, network)
        except BaseException as err:
            if "max_fee must be bigger than 0." in str(err):
                logging.error(
                    """
                    \n😰 Whoops, looks like max fee is missing. Try with:\n
                    --max_fee=`MAX_FEE`
                    """
                )

async def _call_command(command, network):
    args = argparse
    args.feeder_gateway_url = get_feeder_url(network)

    return await capture_stdout(
        call(args=args, command_args=command)
    )

async def _invoke_command(command, network):
    args = argparse
    args.feeder_gateway_url = get_feeder_url(network)
    args.gateway_url = get_gateway_url(network)
    args.wallet = ""
    args.network_id = network
    args.account_dir = None
    args.account = None

    return await capture_stdout(
        invoke(args=args, command_args=command)
    )
