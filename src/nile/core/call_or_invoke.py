"""Command to call or invoke StarkNet smart contracts."""
import logging
import os
import subprocess

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

    if max_fee is not None:
        command.append("--max_fee")
        command.append(max_fee)

    try:
        output = subprocess.check_output(command).strip().decode("utf-8")
        return output

    except subprocess.CalledProcessError:
        p = subprocess.Popen(command, stderr=subprocess.PIPE)
        _, error = p.communicate()

        if "max_fee must be bigger than 0" in error.decode():
            logging.error(
                """
                \n😰 Whoops, looks like max fee is missing. Try with:\n
                --max_fee=`MAX_FEE`
                """
            )
        else:
            raise
