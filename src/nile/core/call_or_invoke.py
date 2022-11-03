"""Command to call or invoke StarkNet smart contracts."""
import logging
import re

from nile import deployments
from nile.common import normalize_number, run_command
from nile.core import account
from nile.utils import hex_address
from nile.utils.status import status


def call_or_invoke(
    contract,
    type,
    method,
    params,
    network,
    signature=None,
    max_fee=None,
    query_flag=None,
    watch_mode=None,
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
    @param query_flag: either simulate or estimate_fee.
    @param watch_mode: either track or debug.
    """
    if isinstance(contract, account.Account):
        address = contract.address
        abi = contract.abi_path
    else:
        address, abi = next(deployments.load(contract, network))

    address = hex_address(address)
    arguments = [
        "--address",
        address,
        "--abi",
        abi,
        "--function",
        method,
    ]

    output = run_command(
        operation=type,
        network=network,
        inputs=params,
        arguments=arguments,
        signature=signature,
        max_fee=max_fee,
        query_flag=query_flag,
    )

    if type != "call" and output:
        logging.info(output)
        if not query_flag and watch_mode:
            transaction_hash = _get_transaction_hash(output)
            return status(normalize_number(transaction_hash), network, watch_mode)

    return output


def _get_transaction_hash(string):
    match = re.search(r"Transaction hash: (0x[\da-f]{1,64})", string)
    return match.groups()[0] if match else None
