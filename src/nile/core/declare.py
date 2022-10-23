"""Command to declare StarkNet smart contracts."""
import logging

from nile import deployments
from nile.common import DECLARATIONS_FILENAME, parse_information, run_command
from nile.utils import hex_address


def declare(
    sender,
    contract_name,
    signature,
    network,
    alias=None,
    overriding_path=None,
    max_fee=None,
):
    """Declare StarkNet smart contracts."""
    logging.info(f"🚀 Declaring {contract_name}")

    if alias_exists(alias, network):
        file = f"{network}.{DECLARATIONS_FILENAME}"
        raise Exception(f"Alias {alias} already exists in {file}")

    arguments = ["--sender", hex_address(sender)]
    max_fee = "0" if max_fee is None else str(max_fee)

    output = run_command(
        operation="declare",
        network=network,
        contract_name=contract_name,
        arguments=arguments,
        signature=signature,
        max_fee=max_fee,
        overriding_path=overriding_path,
    )

    class_hash, tx_hash = parse_information(output)
    logging.info(
        f"⏳ Successfully sent declaration of {contract_name} as {hex(class_hash)}"
    )
    logging.info(f"🧾 Transaction hash: {hex(tx_hash)}")

    deployments.register_class_hash(class_hash, network, alias)
    return class_hash


def alias_exists(alias, network):
    """Return whether an alias exists or not."""
    existing_alias = next(deployments.load_class(alias, network), None)
    return existing_alias is not None
