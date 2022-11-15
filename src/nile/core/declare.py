"""Command to declare StarkNet smart contracts."""
import logging

from nile import deployments
from nile.common import (
    DECLARATIONS_FILENAME,
    call_cli,
    parse_information,
    set_args,
    set_command_args,
)
from nile.utils import hex_address, hex_class_hash
from nile.utils.status import status


async def declare(
    sender,
    contract_name,
    signature,
    network,
    alias=None,
    overriding_path=None,
    max_fee=None,
    mainnet_token=None,
    watch_mode=None,
):
    """Declare StarkNet smart contracts."""
    logging.info(f"🚀 Declaring {contract_name}")

    if alias_exists(alias, network):
        file = f"{network}.{DECLARATIONS_FILENAME}"
        raise Exception(f"Alias {alias} already exists in {file}")

    max_fee = "0" if max_fee is None else str(max_fee)

    args = set_args(network)
    command_args = set_command_args(
        contract_name=contract_name,
        signature=signature,
        max_fee=max_fee,
        overriding_path=overriding_path,
        mainnet_token=mainnet_token,
    )

    command_args += ["--sender", hex_address(sender)]

    output = await call_cli("declare", args, command_args)
    class_hash, tx_hash = parse_information(output)
    padded_hash = hex_class_hash(class_hash)
    logging.info(f"⏳ Successfully sent declaration of {contract_name} as {padded_hash}")
    logging.info(f"🧾 Transaction hash: {hex(tx_hash)}")

    deployments.register_class_hash(padded_hash, network, alias)

    if watch_mode is not None:
        tx_status = await status(tx_hash, network, watch_mode)
        if tx_status.status.is_rejected:
            deployments.unregister(class_hash, network, alias, is_declaration=True)
            return

    return padded_hash


def alias_exists(alias, network):
    """Return whether an alias exists or not."""
    existing_alias = next(deployments.load_class(alias, network), None)
    return existing_alias is not None
