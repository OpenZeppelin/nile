"""Command to deploy StarkNet smart contracts."""
import logging

from nile import deployments
from nile.common import ABIS_DIRECTORY, BUILD_DIRECTORY, parse_information, run_command


def deploy(contract_name, arguments, network, alias, overriding_path=None):
    """Deploy StarkNet smart contracts."""
    logging.info(f"🚀 Deploying {contract_name}")
    base_path = (
        overriding_path if overriding_path else (BUILD_DIRECTORY, ABIS_DIRECTORY)
    )
    abi = f"{base_path[1]}/{contract_name}.json"

    output = run_command(
        operation="deploy",
        network=network,
        contract_name=contract_name,
        overriding_path=overriding_path,
        inputs=arguments,
    )

    address, tx_hash = parse_information(output)
    logging.info(f"⏳ ️Deployment of {contract_name} successfully sent at {address}")
    logging.info(f"🧾 Transaction hash: {tx_hash}")

    deployments.register(address, abi, network, alias)
    return address, abi
