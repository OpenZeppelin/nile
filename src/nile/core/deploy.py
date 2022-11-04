"""Command to deploy StarkNet smart contracts."""
import logging

from nile import deployments
from nile.common import ABIS_DIRECTORY, BUILD_DIRECTORY, parse_information, run_command
from nile.utils import hex_address
from nile.utils.status import status


def deploy(
    contract_name,
    arguments,
    network,
    alias,
    overriding_path=None,
    abi=None,
    mainnet_token=None,
    watch_mode=None,
):
    """Deploy StarkNet smart contracts."""
    logging.info(f"🚀 Deploying {contract_name}")
    base_path = (
        overriding_path if overriding_path else (BUILD_DIRECTORY, ABIS_DIRECTORY)
    )
    register_abi = abi if abi is not None else f"{base_path[1]}/{contract_name}.json"

    output = run_command(
        operation="deploy",
        network=network,
        contract_name=contract_name,
        overriding_path=overriding_path,
        inputs=arguments,
        mainnet_token=mainnet_token,
    )

    address, tx_hash = parse_information(output)
    logging.info(
        f"⏳ ️Deployment of {contract_name} successfully sent at {hex_address(address)}"
    )
    logging.info(f"🧾 Transaction hash: {hex(tx_hash)}")

    deployments.register(address, register_abi, network, alias)

    if watch_mode is not None:
        if status(tx_hash, network, watch_mode).status.is_rejected:
            deployments.unregister(address, network, alias, abi=register_abi)
            return

    return address, register_abi
