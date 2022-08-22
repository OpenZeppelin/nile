"""Command to deploy StarkNet smart contracts."""
import logging

from starkware.starknet.definitions import constants
from starkware.starknet.services.api.contract_class import ContractClass
from starkware.starknet.services.api.gateway.transaction import Deploy
from starkware.starknet.utils.api_utils import cast_to_felts
from starkware.starknet.cli.starknet_cli import get_salt

from nile import deployments
from nile.common import ABIS_DIRECTORY, BUILD_DIRECTORY, get_gateway_response


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

    args = cast_to_felts(arguments or [])
    base_path = (
        overriding_path if overriding_path else (BUILD_DIRECTORY, ABIS_DIRECTORY)
    )
    artifact = f"{base_path[0]}/{contract_name}.json"
    abi = f"{base_path[1]}/{contract_name}.json"

    open_artifact = open(artifact, "r")
    contract_class = ContractClass.loads(data=open_artifact.read())

    tx = Deploy(
        contract_address_salt=get_salt(salt),
        contract_definition=contract_class,
        constructor_calldata=args,
        version=constants.TRANSACTION_VERSION,
    )

    address, tx_hash = await get_gateway_response(network, tx, token, "deploy")

    deployments.register(address, abi, network, alias)
    logging.info(f"⏳ ️Deployment of {contract_name} successfully sent at {address}")
    logging.info(f"🧾 Transaction hash: {tx_hash}")

    return address, abi
