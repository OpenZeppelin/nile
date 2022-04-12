"""Command to call or invoke StarkNet smart contracts."""
import os
import subprocess

from nile import deployments
from nile.common import GATEWAYS


def call_or_invoke(
    contract, type, method, params, network, max_fee=None, signature=None
):
    """Call or invoke functions of StarkNet smart contracts."""
    address, abi = next(deployments.load(contract, network))

    command = [
        "starknet",
        type,
        "--address",
        address,
        "--abi",
        abi,
        "--function",
        method,
    ]

    if network == "mainnet":
        os.environ["STARKNET_NETWORK"] = "alpha-mainnet"
    elif network == "goerli":
        os.environ["STARKNET_NETWORK"] = "alpha-goerli"
    else:
        gateway_prefix = "feeder_gateway" if type == "call" else "gateway"
        command.append(f"--{gateway_prefix}_url={GATEWAYS.get(network)}")

    if len(params) > 0:
        command.append("--inputs")
        command.extend(params)

    if max_fee is not None:
        command.append("--max_fee")
        command.extend(str(max_fee))

    if signature is not None:
        command.append("--signature")
        command.extend(signature)

    return subprocess.check_output(command).strip().decode("utf-8")
