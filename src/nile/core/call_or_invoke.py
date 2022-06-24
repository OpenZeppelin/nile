"""Command to call or invoke StarkNet smart contracts."""
import os
import subprocess

from starkware.starkware_utils.error_handling import StarkException

from nile import deployments
from nile.common import GATEWAYS


def call_or_invoke(
    contract, type, method, params, network, signature=None, max_fee=None
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

    if signature is not None:
        command.append("--signature")
        command.extend(signature)

    command.append("--max_fee")
    command.append(str(max_fee))

    try:
        output = subprocess.check_output(command).strip().decode("utf-8")
        return output
    except StarkException:
        print("")
        print("😰 Whooops, looks like max fee is missing. Try with:\n")
        print("             --max_fee=`MAX_FEE`")
        print("")
