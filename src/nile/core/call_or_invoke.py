"""Command to call or invoke StarkNet smart contracts."""

from nile import deployments
from nile.common import prepare_params, run_command


def call_or_invoke(
    contract, type, method, params, network, signature=None, max_fee=None
):
    """Call or invoke functions of StarkNet smart contracts."""
    address, abi = next(deployments.load(contract, network))

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
