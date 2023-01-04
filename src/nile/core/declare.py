"""Command to declare StarkNet smart contracts."""

import logging

from nile import deployments
from nile.common import DECLARATIONS_FILENAME, parse_information
from nile.utils import hex_class_hash


async def declare(
    transaction,
    signer,
    alias=None,
    watch_mode=None,
):
    """Declare StarkNet smart contracts."""
    contract_name = transaction.contract_to_submit
    network = transaction.network

    logging.info(f"🚀 Declaring {contract_name}")

    if alias_exists(alias, network):
        file = f"{network}.{DECLARATIONS_FILENAME}"
        raise Exception(f"Alias {alias} already exists in {file}")

    tx_status, output = await transaction.execute(signer=signer, watch_mode=watch_mode)

    class_hash, tx_hash = parse_information(output)
    padded_hash = hex_class_hash(class_hash)
    logging.info(f"⏳ Successfully sent declaration of {contract_name} as {padded_hash}")
    logging.info(f"🧾 Transaction hash: {hex(tx_hash)}")

    if not tx_status.status.is_rejected:
        deployments.register_class_hash(class_hash, network, alias)

    return tx_status, padded_hash


def alias_exists(alias, network):
    """Return whether an alias exists or not."""
    existing_alias = next(deployments.load_class(alias, network), None)
    return existing_alias is not None
