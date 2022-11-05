"""Command to deploy StarkNet smart contracts."""
import logging

from nile import deployments
from nile.common import (
    ABIS_DIRECTORY,
    BUILD_DIRECTORY,
    call_cli,
    parse_information,
    set_args,
    set_command_args,
)
from nile.utils import hex_address


async def deploy(
    contract_name,
    arguments,
    network,
    alias,
    overriding_path=None,
    abi=None,
    mainnet_token=None,
):
    """Deploy StarkNet smart contracts."""
    logging.info(f"🚀 Deploying {contract_name}")

    base_path = (
        overriding_path if overriding_path else (BUILD_DIRECTORY, ABIS_DIRECTORY)
    )
    register_abi = abi if abi is not None else f"{base_path[1]}/{contract_name}.json"

    args = set_args(network)
    command_args = set_command_args(
        contract_name=contract_name,
        inputs=arguments,
        overriding_path=overriding_path,
        mainnet_token=mainnet_token,
    )

    output = await call_cli("deploy", args, command_args)
    address, tx_hash = parse_information(output)

    logging.info(
        f"⏳ ️Deployment of {contract_name} successfully sent at {hex_address(address)}"
    )
    logging.info(f"🧾 Transaction hash: {hex(tx_hash)}")

    deployments.register(address, register_abi, network, alias)
    return address, register_abi
