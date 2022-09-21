"""Retrieve and manage deployed accounts."""
import logging
import os
import subprocess

from nile.core.common import get_gateway

GATEWAYS = get_gateway()


def get_nonce(contract_address, network):
    """Get the current nonce for contract address in a given network."""
    command = ["starknet", "get_nonce", "--contract_address", contract_address]

    if network == "mainnet":
        os.environ["STARKNET_NETWORK"] = "alpha-mainnet"
    elif network == "goerli":
        os.environ["STARKNET_NETWORK"] = "alpha-goerli"
    else:
        command.append(f"--feeder_gateway_url={GATEWAYS.get(network)}")

    nonce = int(subprocess.check_output(command).strip())

    logging.info(f"\nCurrent nonce for {contract_address} is {nonce}")
    return nonce
