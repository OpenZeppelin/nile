"""Command to declare StarkNet smart contracts."""
import logging

from nile import deployments
from nile.common import DECLARATIONS_FILENAME, ABIS_DIRECTORY, BUILD_DIRECTORY, GATEWAYS
from starkware.starknet.services.api.gateway.transaction import Declare, DECLARE_SENDER_ADDRESS
from starkware.starknet.services.api.contract_class import ContractClass
from starkware.starknet.definitions import constants
from starkware.starknet.services.api.gateway.gateway_client import GatewayClient
from starkware.starkware_utils.error_handling import StarkErrorCode


async def declare(contract_name, network, alias=None, overriding_path=None, token=None):
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

    tx = Declare(
        contract_class=contract_class,
        sender_address=DECLARE_SENDER_ADDRESS,
        max_fee=0,
        signature=[0],
        nonce=0,
        version=constants.TRANSACTION_VERSION,
    )

    class_hash, tx_hash = await get_gateway_response(network, tx, token, "declaaare")

    logging.info(f"⏳ Declaration of {contract_name} successfully sent at {class_hash}")
    logging.info(f"🧾 Transaction hash: {tx_hash}")

    deployments.register_class_hash(str(class_hash), network, alias)
    return class_hash


def alias_exists(alias, network):
    """Return whether an alias exists or not."""
    existing_alias = next(deployments.load_class(alias, network), None)
    return existing_alias is not None


async def get_gateway_response(network, tx, token, type):
    gateway_client = GatewayClient(url=GATEWAYS.get(network))
    gateway_response = await gateway_client.add_transaction(tx=tx, token=token)

    if gateway_response["code"] != StarkErrorCode.TRANSACTION_RECEIVED.name:
        raise BaseException(
            f"Transaction failed because:\n{gateway_response}."
        )
    if type == "deploy":
        return gateway_response["address"], gateway_response["transaction_hash"]
    elif type == "declare":
        return gateway_response["class_hash"], gateway_response["transaction_hash"]
    else:
        raise TypeError(f"Unknown type '{type}', must be 'deploy' or 'declare'")
