"""Retrieve nonce for a contract."""
import logging

from nile.common import call_cli, set_args


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

    command_args = ["--contract_address", contract_address]
    args = set_args(network)

    output = await call_cli("get_nonce", args, command_args)
    return int(output)
