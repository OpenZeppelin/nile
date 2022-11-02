"""Command to deploy StarkNet smart contracts."""
import logging

from starkware.cairo.common.hash_state import compute_hash_on_elements
from starkware.starknet.core.os.contract_address.contract_address import (
    calculate_contract_address_from_hash,
)

from nile import deployments
from nile.common import (
    ABIS_DIRECTORY,
    BUILD_DIRECTORY,
    get_class_hash,
    parse_information,
    run_command,
)
from nile.utils import hex_address


def deprecated_deploy(
    contract_name, arguments, network, alias, overriding_path=None, abi=None
):
    """Deploy StarkNet smart contracts (deprecated)."""
    logging.info(f"🚀 Deploying {contract_name}")
    base_path = (
        overriding_path if overriding_path else (BUILD_DIRECTORY, ABIS_DIRECTORY)
    )
    register_abi = abi if abi is not None else f"{base_path[1]}/{contract_name}.json"

    output = run_command(
        operation="deploy",
        network=network,
        contract_name=contract_name,
        overriding_path=overriding_path,
        inputs=arguments,
    )

    address, tx_hash = parse_information(output)
    logging.info(
        f"⏳ ️Deployment of {contract_name} successfully sent at {hex_address(address)}"
    )
    logging.info(f"🧾 Transaction hash: {hex(tx_hash)}")

    deployments.register(address, register_abi, network, alias)
    return address, register_abi


def deploy_contract(
    account,
    contract_name,
    salt,
    unique,
    calldata,
    network,
    alias,
    deployer_address,
    max_fee,
    overriding_path=None,
    abi=None,
):
    """Deploy StarkNet smart contracts through UDC."""
    logging.info(f"🚀 Deploying {contract_name}")

    class_hash = get_class_hash(contract_name=contract_name)

    output = account.send(
        to=deployer_address,
        method="deployContract",
        calldata=[class_hash, salt, unique, len(calldata), *calldata],
        max_fee=max_fee,
    )

    base_path = (
        overriding_path if overriding_path else (BUILD_DIRECTORY, ABIS_DIRECTORY)
    )
    register_abi = abi if abi is not None else f"{base_path[1]}/{contract_name}.json"
    deployer_for_address_generation = deployer_address

    if unique:
        # Match UDC address generation
        salt = compute_hash_on_elements(data=[account.address, salt])
        deployer_for_address_generation = 0

    address = calculate_contract_address_from_hash(
        salt, class_hash, calldata, deployer_for_address_generation
    )

    logging.info(
        f"⏳ ️Deployment of {contract_name} successfully sent at {hex_address(address)}"
    )
    # TODO: Get transaction hash from output
    logging.info(f"🧾 Transaction hash: {output}")

    deployments.register(address, register_abi, network, alias)
    return address, register_abi
