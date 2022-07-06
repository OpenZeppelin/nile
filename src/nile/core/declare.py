"""Command to declare StarkNet smart contracts."""
import logging

from nile import deployments
from nile.common import DECLARATIONS_FILENAME, parse_information, run_command


def declare(contract_name, network, alias=None, overriding_path=None):
    """Declare StarkNet smart contracts."""
    logging.info(f"🚀 Declaring {contract_name}")

    if alias_exists(alias, network):
        file = f"{network}.{DECLARATIONS_FILENAME}"
        raise Exception(f"Alias {alias} already exists in {file}")

    output = run_command(contract_name, network, overriding_path, operation="declare")
    class_hash, tx_hash = parse_information(output)
    logging.info(f"⏳ Declaration of {contract_name} successfully sent at {class_hash}")
    logging.info(f"🧾 Transaction hash: {tx_hash}")

    deployments.register_class_hash(class_hash, network, alias)
    return class_hash


def alias_exists(alias, network):
    """Return whether an alias exists or not."""
    existing_alias = next(deployments.load_class(alias, network), None)
    return existing_alias is not None
