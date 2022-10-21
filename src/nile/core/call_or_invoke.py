"""Command to call or invoke StarkNet smart contracts."""

from nile import deployments
from nile.common import run_command
from nile.core import account
from nile.utils import hex_address


def call_or_invoke(
    contract, type, method, params, network, signature=None, max_fee=None
):
    """Call or invoke functions of StarkNet smart contracts."""
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
    )
