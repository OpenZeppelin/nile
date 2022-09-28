"""Command to deploy StarkNet smart contracts."""
import logging

from nile import deployments
from nile.common import ABIS_DIRECTORY, BUILD_DIRECTORY, parse_information, run_command
from nile.utils import hex_address


def deploy(contract_name, arguments, network, alias, overriding_path=None, abi=None):
    """Deploy StarkNet smart contracts."""
    logging.info(f"🚀 Deploying {contract_name}")
    base_path = (
        overriding_path if overriding_path else (BUILD_DIRECTORY, ABIS_DIRECTORY)
    )
    register_abi = abi if abi is not None else f"{base_path[1]}/{contract_name}.json"

    output = run_command(contract_name, network, overriding_path, arguments=arguments)

    address, tx_hash = parse_information(output)
    logging.info(
        f"⏳ ️Deployment of {contract_name} successfully sent at {hex_address(address)}"
    )
    logging.info(f"🧾 Transaction hash: {hex(tx_hash)}")

    deployments.register(address, register_abi, network, alias)
    return address, register_abi
