"""Command to declare StarkNet smart contracts."""
import logging

from starkware.starknet.cli import starknet_cli

from nile import deployments
from nile.common import (
    ABIS_DIRECTORY,
    BUILD_DIRECTORY,
    DECLARATIONS_FILENAME,
    capture_stdout,
    parse_information,
    prepare_params,
    set_args,
)
from nile.utils import hex_address


async def declare(
    sender,
    contract_name,
    signature,
    network,
    alias=None,
    overriding_path=None,
    max_fee=None,
    mainnet_token=None,
):
    """Declare StarkNet smart contracts."""
    logging.info(f"🚀 Declaring {contract_name}")

    if alias_exists(alias, network):
        file = f"{network}.{DECLARATIONS_FILENAME}"
        raise Exception(f"Alias {alias} already exists in {file}")

    base_path = (
        overriding_path if overriding_path else (BUILD_DIRECTORY, ABIS_DIRECTORY)
    )
    contract = f"{base_path[0]}/{contract_name}.json"

    max_fee = "0" if max_fee is None else str(max_fee)

    command_args = [
        "--contract",
        contract,
        "--sender",
        hex_address(sender),
        "--max_fee",
        max_fee,
    ]

    if signature is not None:
        command_args.append("--signature")
        command_args.extend(prepare_params(signature))

    if mainnet_token is not None:
        command_args.apend("--token")
        command_args.extend(mainnet_token)

    args = set_args(network)

    output = await capture_stdout(
        starknet_cli.declare(args=args, command_args=command_args)
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
