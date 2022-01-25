"""Command to deploy StarkNet smart contracts."""
import logging
import os
import re
import subprocess

from nile import deployments
from nile.common import ABIS_DIRECTORY, BUILD_DIRECTORY, GATEWAYS


def deploy(contract_name, arguments, network, alias, overriding_path=None):
    """Deploy StarkNet smart contracts."""
    logging.info(f"🚀 Deploying {contract_name}")

    base_path = (
        overriding_path if overriding_path else (BUILD_DIRECTORY, ABIS_DIRECTORY)
    )
    contract = f"{base_path[0]}/{contract_name}.json"
    abi = f"{base_path[1]}/{contract_name}.json"

    command = ["starknet", "deploy", "--contract", contract]

    if len(arguments) > 0:
        command.append("--inputs")
        command.extend([argument for argument in arguments])

    if network == "mainnet":
        os.environ["STARKNET_NETWORK"] = "alpha-mainnet"
    elif network == "goerli":
        os.environ["STARKNET_NETWORK"] = "alpha-goerli"
    else:
        command.append(f"--gateway_url={GATEWAYS.get(network)}")

    output = subprocess.check_output(command)
    address, tx_hash = parse_deployment(output)
    logging.info(f"⏳ ️Deployment of {contract_name} successfully sent at {address}")
    logging.info(f"🧾 Transaction hash: {tx_hash}")

    deployments.register(address, abi, network, alias)
    return address, abi


def parse_deployment(x):
    """Extract information from deployment command."""
    # address is 64, tx_hash is 64 chars long
    address, tx_hash = re.findall("0x[\\da-f]{1,64}", str(x))
    return address, tx_hash
