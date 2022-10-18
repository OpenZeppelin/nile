"""Retrieve nonce for a contract."""
import logging

from starkware.starknet.cli import starknet_cli

from nile.common import Args, get_feeder_url, capture_stdout


async def get_nonce(contract_address, network):
    """Get the current nonce for contract address in a given network."""
    nonce = await get_nonce_without_log(contract_address, network)

    logging.info(f"Current Nonce: {nonce}")

    return nonce


async def get_nonce_without_log(contract_address, network):
    """Get the current nonce without logging."""
    # Starknet CLI requires a hex string for get_nonce command
    if not str(contract_address).startswith("0x"):
        contract_address = hex(int(contract_address))

    command = ["--contract_address", contract_address]

    args = Args()
    args.feeder_gateway_url = get_feeder_url(network)

    return await capture_stdout(
        starknet_cli.get_nonce(args=args, command_args=command)
    )
