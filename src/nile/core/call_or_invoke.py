"""Command to call or invoke StarkNet smart contracts."""

from nile import deployments
from nile.common import run_command
from nile.core import account
from nile.utils import hex_address


def call_or_invoke(
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
    arguments = [
        "--address",
        address,
        "--abi",
        abi,
        "--function",
        method,
    ]

    return run_command(
        operation=type,
        network=network,
        inputs=params,
        arguments=arguments,
        signature=signature,
        max_fee=max_fee,
        query_flag=query_flag,
    )
