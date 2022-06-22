"""Command to declare StarkNet smart contracts."""
import logging
import re

from nile import deployments
from nile.common import run_command


def declare(contract_name, network, alias=None, overriding_path=None):
    """Deploy StarkNet smart contracts."""
    logging.info(f"🚀 Declaring {contract_name}")

    output = run_command(contract_name, network, overriding_path, operation="declare")
    class_hash, tx_hash = parse_declaration(output)
    logging.info(f"⏳ Declaration of {contract_name} successfully sent at {class_hash}")
    logging.info(f"🧾 Transaction hash: {tx_hash}")

    deployments.register_class_hash(class_hash, network, alias)
    return class_hash


def parse_declaration(x):
    """Extract information from deployment command."""
    # class_hash is 64, tx_hash is 64 chars long
    class_hash, tx_hash = re.findall("0x[\\da-f]{1,64}", str(x))
    return class_hash, tx_hash
