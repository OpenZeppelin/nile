"""Command to deploy StarkNet smart contracts."""
import logging

from starkware.cairo.common.hash_chain import compute_hash_chain
from starkware.starknet.core.os.contract_address.contract_address import (
    calculate_contract_address_from_hash,
)

from nile import deployments
from nile.common import (
    ABIS_DIRECTORY,
    BUILD_DIRECTORY,
    get_class_hash,
    parse_information,
)
from nile.starknet_cli import execute_call
from nile.utils import hex_address
from nile.utils.status import status


async def deploy(
    contract_name,
    arguments,
    network,
    alias,
    overriding_path=None,
    abi=None,
    mainnet_token=None,
    watch_mode=None,
):
    """Deploy StarkNet smart contracts (DEPRECATED)."""
    logging.info(
        f"🚀 Deploying {contract_name} without Account. "
        + "This method is deprecated and will be removed soon. "
        + "Use the --account option."
    )
    base_path = (
        overriding_path if overriding_path else (BUILD_DIRECTORY, ABIS_DIRECTORY)
    )
    register_abi = abi if abi is not None else f"{base_path[1]}/{contract_name}.json"

    output = await execute_call(
        "deploy",
        network,
        contract_name=contract_name,
        inputs=arguments,
        overriding_path=overriding_path,
        mainnet_token=mainnet_token,
    )
    address, tx_hash = parse_information(output)

    logging.info(
        f"⏳ ️Deployment of {contract_name} successfully sent at {hex_address(address)}"
    )
    logging.info(f"🧾 Transaction hash: {hex(tx_hash)}")

    deployments.register(address, register_abi, network, alias)

    if watch_mode is not None:
        tx_status = await status(tx_hash, network, watch_mode)
        if tx_status.status.is_rejected:
            deployments.unregister(address, network, alias, abi=register_abi)
            return

    return address, register_abi


async def deploy_contract(
    account,
    contract_name,
    salt,
    unique,
    calldata,
    alias,
    deployer_address,
    max_fee,
    overriding_path=None,
    abi=None,
    watch_mode=None,
):
    """Deploy StarkNet smart contracts."""
    logging.info(f"🚀 Deploying {contract_name}")

    base_path = (
        overriding_path if overriding_path else (BUILD_DIRECTORY, ABIS_DIRECTORY)
    )
    register_abi = abi if abi is not None else f"{base_path[1]}/{contract_name}.json"
    deployer_for_address_generation = 0

    if salt is None:
        salt = 0

    _salt = salt

    if unique:
        # Match UDC address generation
        _salt = compute_hash_chain(data=[account.address, salt])
        deployer_for_address_generation = deployer_address

    class_hash = get_class_hash(contract_name=contract_name)

    address = calculate_contract_address_from_hash(
        _salt, class_hash, calldata, deployer_for_address_generation
    )

    output = await account.send(
        deployer_address,
        method="deployContract",
        calldata=[class_hash, salt, unique, len(calldata), *calldata],
        max_fee=max_fee,
    )

    _, tx_hash = parse_information(output)
    logging.info(
        f"⏳ ️Deployment of {contract_name} successfully sent at {hex_address(address)}"
    )
    logging.info(f"🧾 Transaction hash: {hex(tx_hash)}")

    deployments.register(address, register_abi, account.network, alias)

    if watch_mode is not None:
        tx_status = await status(tx_hash, account.network, watch_mode)
        if tx_status.status.is_rejected:
            deployments.unregister(address, account.network, alias, abi=register_abi)
            return

    return address, register_abi
