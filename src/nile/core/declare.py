"""Command to deploy StarkNet smart contracts."""
import logging
import os
import re
import subprocess

from nile import deployments
from nile.common import ABIS_DIRECTORY, BUILD_DIRECTORY, GATEWAYS


def declare(contract_name, network, alias=None, overriding_path=None):
    """Deploy StarkNet smart contracts."""
    logging.info(f"🚀 Declaring {contract_name}")

    command = ["starknet", "declare", "--contract", contract]

    if network == "mainnet":
        os.environ["STARKNET_NETWORK"] = "alpha-mainnet"
    elif network == "goerli":
        os.environ["STARKNET_NETWORK"] = "alpha-goerli"
    else:
        command.append(f"--gateway_url={GATEWAYS.get(network)}")

    output = subprocess.check_output(command)
    address, tx_hash = parse_deployment(output)
    logging.info(f"⏳ Declaration of {contract_name} successfully sent at {address}")
    logging.info(f"🧾 Transaction hash: {tx_hash}")

    declarations.register_class_hash(address, network, alias)
    return address


def parse_deployment(x):
    """Extract information from deployment command."""
    # address is 64, tx_hash is 64 chars long
    address, tx_hash = re.findall("0x[\\da-f]{1,64}", str(x))
    return address, tx_hash
