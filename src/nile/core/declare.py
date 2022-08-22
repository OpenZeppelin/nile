"""Command to declare StarkNet smart contracts."""
import logging

from starkware.starknet.definitions import constants
from starkware.starknet.services.api.contract_class import ContractClass
from starkware.starknet.services.api.gateway.transaction import (
    DECLARE_SENDER_ADDRESS,
    Declare,
)

from nile import deployments
from nile.common import (
    ABIS_DIRECTORY,
    BUILD_DIRECTORY,
    DECLARATIONS_FILENAME,
    get_gateway_response,
)


async def declare(
    contract_name, network, alias=None, signature=None, overriding_path=None, token=None
):
    """Declare StarkNet smart contracts."""
    logging.info(f"🚀 Declaring {contract_name}")

    if alias_exists(alias, network):
        file = f"{network}.{DECLARATIONS_FILENAME}"
        raise Exception(f"Alias {alias} already exists in {file}")

    base_path = (
        overriding_path if overriding_path else (BUILD_DIRECTORY, ABIS_DIRECTORY)
    )
    artifact = f"{base_path[0]}/{contract_name}.json"
    open_artifact = open(artifact, "r")
    contract_class = ContractClass.loads(data=open_artifact.read())

    if signature is None:
        signature = []

    tx = Declare(
        contract_class=contract_class,
        sender_address=DECLARE_SENDER_ADDRESS,
        signature=signature,
        nonce=0,
        max_fee=0,
        version=constants.TRANSACTION_VERSION,
    )

    class_hash, tx_hash = await get_gateway_response(network, tx, token, "declare")

    deployments.register_class_hash(class_hash, network, alias)
    logging.info(f"⏳ Declaration of {artifact} successfully sent at {class_hash}")
    logging.info(f"🧾 Transaction hash: {tx_hash}")

    return class_hash


def alias_exists(alias, network):
    """Return whether an alias exists or not."""
    existing_alias = next(deployments.load_class(alias, network), None)
    return existing_alias is not None
