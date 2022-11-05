"""Command to deploy StarkNet smart contracts."""
import logging

from starkware.starknet.cli import starknet_cli
from starkware.starknet.services.api.gateway.transaction import DeployAccount

from nile import deployments
from nile.common import (
    ABIS_DIRECTORY,
    BUILD_DIRECTORY,
    QUERY_VERSION,
    TRANSACTION_VERSION,
    capture_stdout,
    get_gateway_response,
    get_hash,
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

    output = await capture_stdout(
        starknet_cli.deploy(args=args, command_args=command_args)
    )

    address, tx_hash = parse_information(output)
    logging.info(
        f"⏳ ️Deployment of {contract_name} successfully sent at {hex_address(address)}"
    )
    logging.info(f"🧾 Transaction hash: {hex(tx_hash)}")

    deployments.register(address, register_abi, network, alias)
    return address, register_abi


async def deploy_account(
    network,
    salt,
    calldata,
    signature,
    contract_name="Account",
    max_fee=None,
    nonce=0,
    abi=None,
    overriding_path=None,
    alias=None,
    query_type=None,
    mainnet_token=None,
):
    """Deploy StarkNet smart contracts."""
    logging.info(f"🚀 Deploying {contract_name}")

    tx_version = QUERY_VERSION if query_type else TRANSACTION_VERSION
    base_path = (
        overriding_path if overriding_path else (BUILD_DIRECTORY, ABIS_DIRECTORY)
    )
    register_abi = abi if abi is not None else f"{base_path[1]}/{contract_name}.json"

    class_hash = get_hash(contract_name)

    tx = DeployAccount(
        class_hash=class_hash,
        constructor_calldata=calldata,
        contract_address_salt=salt,
        max_fee=max_fee,
        nonce=nonce,
        signature=signature,
        version=tx_version,
    )

    response = await get_gateway_response(network, tx, mainnet_token)
    address = response["address"]
    tx_hash = response["tx_hash"]

    logging.info(
        f"⏳ ️Deployment of {contract_name} successfully sent at {hex_address(address)}"
    )
    logging.info(f"🧾 Transaction hash: {hex(tx_hash)}")

    deployments.register(address, register_abi, network, alias)
    return address, register_abi
