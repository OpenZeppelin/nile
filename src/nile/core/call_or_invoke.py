"""Command to call or invoke StarkNet smart contracts."""
import logging
import re

from nile import deployments
from nile.common import is_alias
from nile.starknet_cli import execute_call
from nile.utils import hex_address, normalize_number
from nile.utils.status import status


async def call_or_invoke(
    contract,
    type,
    method,
    params,
    network,
    abi=None,
    signature=None,
    max_fee=None,
    query_flag=None,
    watch_mode=None,
):
    """
    Call or invoke functions of StarkNet smart contracts.

    @param contract: can be an address or an alias.
    @param type: can be either call or invoke.
    @param method: the targeted function.
    @param params: the targeted function arguments.
    @param network: goerli, goerli2, integration, mainnet, or predefined networks file.
    @param signature: optional signature for invoke transactions.
    @param max_fee: optional max fee for invoke transactions.
    @param query_flag: either simulate or estimate_fee.
    @param watch_mode: either track or debug.
    """
    if abi is None or is_alias(contract):
        address, abi = next(deployments.load(contract, network))
    else:
        address = contract

    try:
        output = await execute_call(
            type,
            network,
            inputs=params,
            signature=signature,
            max_fee=max_fee,
            query_flag=query_flag,
            address=hex_address(address),
            abi=abi,
            method=method,
        )
    except BaseException as err:
        if "max_fee must be bigger than 0." in str(err):
            logging.error(
                """
                \n😰 Whoops, looks like max fee is missing. Try with:\n
                --max_fee=`MAX_FEE`
                """
            )
            return
        else:
            logging.error(err)
            return

    if type != "call" and output:
        logging.info(output)
        if not query_flag and watch_mode:
            transaction_hash = _get_transaction_hash(output)
            return await status(normalize_number(transaction_hash), network, watch_mode)

    return output


def _get_transaction_hash(string):
    match = re.search(r"Transaction hash: (0x[\da-f]{1,64})", string)
    return match.groups()[0] if match else None
