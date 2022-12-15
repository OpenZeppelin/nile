"""Retrieve nonce for a contract."""
import logging

from nile.starknet_cli import execute_call


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

    output = await execute_call("get_nonce", network, contract_address=contract_address)
    return int(output)
