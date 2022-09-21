"""Retrieve nonce for a contract."""
import logging
import os
import subprocess

from nile.common import get_gateway

GATEWAYS = get_gateway()


def get_nonce(contract_address, network):
    """Get the current nonce for contract address in a given network."""
    nonce = get_nonce_without_log(contract_address, network)

    logging.info(f"Current Nonce: {nonce}")

    return nonce


def get_nonce_without_log(contract_address, network):
    """Get the current nonce without logging."""
    # Starknet CLI requires an hex string for get nonce command
    if type(contract_address) == int:
        contract_address = hex(contract_address)

    command = ["starknet", "get_nonce", "--contract_address", contract_address]

    if network == "mainnet":
        os.environ["STARKNET_NETWORK"] = "alpha-mainnet"
    elif network == "goerli":
        os.environ["STARKNET_NETWORK"] = "alpha-goerli"
    else:
        command.append(f"--feeder_gateway_url={GATEWAYS.get(network)}")

    return int(subprocess.check_output(command).strip())
