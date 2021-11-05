"""Command to deploy StarkNet smart contracts."""
import os
import subprocess

from nile import deployments
from nile.common import DEPLOYMENTS_FILENAME

GATEWAYS = {"localhost": "http://localhost:5000/"}


def invoke_command(contract, method, params, network):
    """Invoke functions of StarkNet smart contracts."""
    address, abi = next(deployments.load(contract, network))

    command = [
        "starknet",
        "invoke",
        "--address",
        address,
        "--abi",
        abi,
        "--function",
        method,
    ]

    if network == "mainnet":
        os.environ["STARKNET_NETWORK"] = "alpha"
    else:
        command.append(f"--gateway_url={GATEWAYS.get(network)}")

    if len(params) > 0:
        command.append("--inputs")
        command.extend([param for param in params])

    subprocess.check_call(command)
