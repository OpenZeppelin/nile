"""Command to deploy StarkNet smart contracts."""

import logging

from nile import accounts, deployments
from nile.common import ABIS_DIRECTORY, BUILD_DIRECTORY
from nile.utils import hex_address


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
