"""Command to deploy StarkNet smart contracts."""
import logging

from starkware.starknet.services.api.gateway.transaction import DeployAccount

from nile import deployments
from nile.common import (
    ABIS_DIRECTORY,
    BUILD_DIRECTORY,
    QUERY_VERSION,
    TRANSACTION_VERSION,
    get_account_class_hash,
    parse_information,
)
from nile.starknet_cli import execute_call, get_gateway_response
from nile.utils import hex_address
from nile.utils.status import status


async def deploy(
    contract_name,
    arguments,
    network,
    alias,
    overriding_path=None,
    abi=None,
    mainnet_token=None,
    watch_mode=None,
):
    """Deploy StarkNet smart contracts (DEPRECATED)."""
    logging.info(
        f"🚀 Deploying {contract_name} without Account. "
        + "This method is deprecated and will be removed soon. "
        + "Use the --account option."
    )
    base_path = (
        overriding_path if overriding_path else (BUILD_DIRECTORY, ABIS_DIRECTORY)
    )
    register_abi = abi if abi is not None else f"{base_path[1]}/{contract_name}.json"

    output = await execute_call(
        "deploy",
        network,
        contract_name=contract_name,
        inputs=arguments,
        overriding_path=overriding_path,
        mainnet_token=mainnet_token,
    )
    address, tx_hash = parse_information(output)

    logging.info(
        f"⏳ ️Deployment of {contract_name} successfully sent at {hex_address(address)}"
    )
    logging.info(f"🧾 Transaction hash: {hex(tx_hash)}")

    deployments.register(address, register_abi, network, alias)

    if watch_mode is not None:
        tx_status = await status(tx_hash, network, watch_mode)
        if tx_status.status.is_rejected:
            deployments.unregister(address, network, alias, abi=register_abi)
            return

    return address, register_abi


async def deploy_contract(
    transaction,
    signer,
    alias,
    overriding_path=None,
    abi=None,
    watch_mode=None,
):
    """Deploy StarkNet smart contracts."""
    network = transaction.network
    contract_name = transaction.contract_to_submit

    logging.info(f"🚀 Deploying {contract_name}")

    base_path = (
        overriding_path if overriding_path else (BUILD_DIRECTORY, ABIS_DIRECTORY)
    )
    register_abi = abi if abi is not None else f"{base_path[1]}/{contract_name}.json"

    # Execute the transaction
    tx_status, output = await transaction.execute(signer=signer, watch_mode=watch_mode)

    address = transaction.udc_deployment_address()

    if not tx_status.status.is_rejected:
        deployments.register(address, register_abi, network, alias)
        logging.info(
            f"⏳ ️Deployment of {contract_name} "
            + f"successfully sent at {hex_address(address)}"
        )
        logging.info(f"🧾 Transaction hash: {hex(tx_status.tx_hash)}")

    return tx_status, address, register_abi


async def deploy_account(
    network,
    salt,
    calldata,
    signature,
    contract_name="Account",
    max_fee=None,
    abi=None,
    overriding_path=None,
    alias=None,
    query_type=None,
    mainnet_token=None,
    watch_mode=None,
):
    """Deploy StarkNet smart contracts."""
    logging.info(f"🚀 Deploying {contract_name}")

    tx_version = QUERY_VERSION if query_type else TRANSACTION_VERSION
    base_path = (
        overriding_path if overriding_path else (BUILD_DIRECTORY, ABIS_DIRECTORY)
    )
    register_abi = abi if abi is not None else f"{base_path[1]}/{contract_name}.json"

    class_hash = get_account_class_hash(contract_name)

    tx = DeployAccount(
        class_hash=class_hash,
        constructor_calldata=calldata,
        contract_address_salt=salt,
        max_fee=max_fee,
        nonce=0,
        signature=signature,
        version=tx_version,
    )

    response = await get_gateway_response(network, tx, mainnet_token)

    address = response["address"]
    tx_hash = response["transaction_hash"]

    logging.info(
        f"⏳ ️Deployment of {contract_name} successfully sent at {hex_address(address)}"
    )
    logging.info(f"🧾 Transaction hash: {tx_hash}")

    deployments.register(address, register_abi, network, alias)

    if watch_mode is not None:
        tx_status = await status(tx_hash, network, watch_mode)
        if tx_status.status.is_rejected:
            deployments.unregister(address, network, alias, abi=register_abi)
            return

    return address, tx_hash, register_abi
