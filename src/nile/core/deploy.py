"""Command to deploy StarkNet smart contracts."""
import logging

from starkware.starknet.definitions import constants, fields
from starkware.starknet.services.api.contract_class import ContractClass
from starkware.starknet.services.api.gateway.gateway_client import GatewayClient
from starkware.starknet.services.api.gateway.transaction import Deploy
from starkware.starknet.utils.api_utils import cast_to_felts
from starkware.starkware_utils.error_handling import StarkErrorCode

from nile import deployments
from nile.common import ABIS_DIRECTORY, BUILD_DIRECTORY, GATEWAYS


async def deploy(
    contract_name,
    arguments,
    network,
    alias,
    overriding_path=None,
    salt=None,
    token=None,
):
    """Deploy StarkNet smart contracts."""
    logging.info(f"🚀 Deploying {contract_name}")

    salt = sanitize_salt(salt)
    args = cast_to_felts(arguments or [])
    base_path = (
        overriding_path if overriding_path else (BUILD_DIRECTORY, ABIS_DIRECTORY)
    )
    artifact = f"{base_path[0]}/{contract_name}.json"
    abi = f"{base_path[1]}/{contract_name}.json"

    open_artifact = open(artifact, "r")
    contract_class = ContractClass.loads(data=open_artifact.read())

    tx = Deploy(
        contract_address_salt=salt,
        contract_definition=contract_class,
        constructor_calldata=args,
        version=constants.TRANSACTION_VERSION,
    )

    address, tx_hash = await get_gateway_response(network, tx, token)

    logging.info(f"⏳ ️Deployment of {contract_name} successfully sent at {address}")
    logging.info(f"🧾 Transaction hash: {tx_hash}")

    deployments.register(address, abi, network, alias)
    return address, abi


async def get_gateway_response(network, tx, token):
    gateway_client = GatewayClient(url=GATEWAYS.get(network))
    gateway_response = await gateway_client.add_transaction(tx=tx, token=token)

    if gateway_response["code"] != StarkErrorCode.TRANSACTION_RECEIVED.name:
        raise BaseException(
            message=f"Failed to send transaction. Response: {gateway_response}."
        )
    return gateway_response["address"], gateway_response["transaction_hash"]


def sanitize_salt(salt):
    if salt is not None:
        assert salt.startswith("0x"), f"salt value '{salt}' should start with '0x'."
    try:
        salt = (
            fields.ContractAddressSalt.get_random_value()
            if salt is None
            else int(salt, 16)
        )
    except ValueError as e:
        raise ValueError("Invalid salt format.") from e
    return salt
