"""Command to deploy StarkNet smart contracts."""
import logging

from nile import deployments
from nile.common import (
    ABIS_DIRECTORY,
    BUILD_DIRECTORY,
    call_cli,
    parse_information,
    prepare_params,
    set_args,
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

    contract = f"{base_path[0]}/{contract_name}.json"
    command_args = ["--contract", contract]

    if arguments:
        command_args.append("--inputs")
        command_args.extend(prepare_params(arguments))

    if mainnet_token:
        command_args.append("--token")
        command_args.extend(mainnet_token)

    args = set_args(network)

    output = await call_cli("deploy", args, command_args)

    address, tx_hash = parse_information(output)
    logging.info(
        f"⏳ ️Deployment of {contract_name} successfully sent at {hex_address(address)}"
    )
    logging.info(f"🧾 Transaction hash: {hex(tx_hash)}")

    deployments.register(address, register_abi, network, alias)
    return address, register_abi
