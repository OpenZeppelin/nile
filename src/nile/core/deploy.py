"""Command to deploy StarkNet smart contracts."""
import logging

from nile import accounts, deployments
from nile.common import ABIS_DIRECTORY, BUILD_DIRECTORY, parse_information
from nile.starknet_cli import execute_call
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
    contract_name,
    alias,
    predicted_address,
    overriding_path=None,
    abi=None,
    watch_mode=None,
):
    """Deploy StarkNet smart contracts."""
    network = transaction.network

    logging.info(f"🚀 Deploying {contract_name}")

    base_path = (
        overriding_path if overriding_path else (BUILD_DIRECTORY, ABIS_DIRECTORY)
    )
    register_abi = abi if abi is not None else f"{base_path[1]}/{contract_name}.json"

    # Execute the transaction
    tx_status, output = await transaction.execute(signer=signer, watch_mode=watch_mode)

    if not tx_status.status.is_rejected:
        deployments.register(predicted_address, register_abi, network, alias)
        logging.info(
            f"⏳ ️Deployment of {contract_name} "
            + f"successfully sent at {hex_address(predicted_address)}"
        )
        logging.info(f"🧾 Transaction hash: {hex(tx_status.tx_hash)}")

    return tx_status, predicted_address, register_abi


async def deploy_account(
    transaction,
    account,
    contract_name,
    alias,
    predicted_address,
    overriding_path=None,
    abi=None,
    watch_mode=None,
):
    """Deploy StarkNet account."""
    network = transaction.network
    logging.info(f"🚀 Deploying {contract_name}")

    base_path = (
        overriding_path if overriding_path else (BUILD_DIRECTORY, ABIS_DIRECTORY)
    )
    register_abi = abi if abi is not None else f"{base_path[1]}/{contract_name}.json"

    # Execute the transaction
    tx_status, _ = await transaction.execute(
        signer=account.signer, watch_mode=watch_mode
    )

    if not tx_status.status.is_rejected:
        # Update Account
        account.address = predicted_address
        account.index = accounts.current_index(network)

        deployments.register(predicted_address, register_abi, network, alias)
        accounts.register(
            account.signer.public_key, predicted_address, account.index, alias, network
        )
        logging.info(
            f"⏳ ️Deployment of {contract_name} successfully"
            + f" sent at {hex_address(predicted_address)}"
        )
        logging.info(f"🧾 Transaction hash: {hex(tx_status.tx_hash)}")

    return tx_status, predicted_address, register_abi
