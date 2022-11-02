"""Command to call or invoke StarkNet smart contracts."""
import logging

from starkware.starknet.cli.starknet_cli import AbiFormatError, call, invoke

from nile import deployments
from nile.common import capture_stdout, prepare_params, set_args
from nile.core import account
from nile.utils import hex_address


async def call_or_invoke(
    contract,
    type,
    method,
    params,
    network,
    signature=None,
    max_fee=None,
    query_flag=None,
):
    """
    Call or invoke functions of StarkNet smart contracts.

    @param contract: can be an address, an alias, or an Account instance.
    @param type: can be either call or invoke.
    @param method: the targeted function.
    @param params: the targeted function arguments.
    @param network: goerli, mainnet, or predefined networks file.
    @param signature: optional signature for invoke transactions.
    @param max_fee: optional max fee for invoke transactions.
    @param query_flag: either simulate or estimate_fee
    """
    if isinstance(contract, account.Account):
        address = contract.address
        abi = contract.abi_path
    else:
        address, abi = next(deployments.load(contract, network))

    address = hex_address(address)
    command_args = [
        "--address",
        address,
        "--abi",
        abi,
        "--function",
        method,
    ]

    if len(params) > 0:
        command_args.append("--inputs")
        command_args.extend(prepare_params(params))

    if signature is not None:
        command_args.append("--signature")
        command_args.extend(prepare_params(signature))

    if max_fee is not None:
        command_args.append("--max_fee")
        command_args.append(max_fee)

    if query_flag is not None:
        command_args.append(f"--{query_flag}")

    args = set_args(network)

    if type == "call":
        try:
            return await capture_stdout(call(args=args, command_args=command_args))
        except AbiFormatError as err:
            logging.error(err)

    elif type == "invoke":
        try:
            return await capture_stdout(invoke(args=args, command_args=command_args))
        except BaseException as err:
            if "max_fee must be bigger than 0." in str(err):
                logging.error(
                    """
                    \n😰 Whoops, looks like max fee is missing. Try with:\n
                    --max_fee=`MAX_FEE`
                    """
                )
            else:
                raise err
