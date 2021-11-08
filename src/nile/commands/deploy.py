"""Command to deploy StarkNet smart contracts."""
import os
import subprocess

from nile import deployments
from nile.common import ABIS_DIRECTORY, BUILD_DIRECTORY, get_address_from

GATEWAYS = {"localhost": "http://localhost:5000/"}


def deploy_command(contract_name, network, alias):
    """Deploy StarkNet smart contracts."""
    print(f"🚀 Deploying {contract_name}")

    contract = f"{BUILD_DIRECTORY}/{contract_name}.json"
    abi = f"{ABIS_DIRECTORY}/{contract_name}.json"

    command = ["starknet", "deploy", "--contract", contract]

    if network == "mainnet":
        os.environ["STARKNET_NETWORK"] = "alpha"
    else:
        command.append(f"--gateway_url={GATEWAYS.get(network)}")

    output = subprocess.check_output(command)
    address = get_address_from(output)
    print(f"🌕 {contract} successfully deployed to {address}")

    deployments.register(address, abi, network, alias)
