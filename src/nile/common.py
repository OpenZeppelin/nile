"""nile common module."""
import json
import os
import re

from starkware.starknet.cli.starknet_cli import NETWORKS
from starkware.starknet.services.api.feeder_gateway.feeder_gateway_client import (
    FeederGatewayClient,
)
from starkware.starknet.services.api.gateway.gateway_client import GatewayClient
from starkware.starkware_utils.error_handling import StarkErrorCode

CONTRACTS_DIRECTORY = "contracts"
BUILD_DIRECTORY = "artifacts"
TEMP_DIRECTORY = ".temp"
ABIS_DIRECTORY = f"{BUILD_DIRECTORY}/abis"
DEPLOYMENTS_FILENAME = "deployments.txt"
DECLARATIONS_FILENAME = "declarations.txt"
ACCOUNTS_FILENAME = "accounts.json"
NODE_FILENAME = "node.json"
RETRY_AFTER_SECONDS = 30


def _get_gateway():
    """Get the StarkNet node details."""
    try:
        with open(NODE_FILENAME, "r") as f:
            gateway = json.load(f)
            return gateway

    except FileNotFoundError:
        with open(NODE_FILENAME, "w") as f:
            f.write('{"localhost": "http://127.0.0.1:5050/"}')


GATEWAYS = _get_gateway()


def get_all_contracts(ext=None, directory=None):
    """Get all cairo contracts in the default contract directory."""
    if ext is None:
        ext = ".cairo"

    files = list()
    for (dirpath, _, filenames) in os.walk(
        directory if directory else CONTRACTS_DIRECTORY
    ):
        files += [
            os.path.join(dirpath, file) for file in filenames if file.endswith(ext)
        ]

    return files


async def get_gateway_response(network, tx, token):
    """Execute transaction and return response."""
    gateway_url = get_gateway_url(network)
    gateway_client = GatewayClient(url=gateway_url)
    gateway_response = await gateway_client.add_transaction(tx=tx, token=token)

    if gateway_response["code"] != StarkErrorCode.TRANSACTION_RECEIVED.name:
        raise BaseException(f"Transaction failed because:\n{gateway_response}.")

    return gateway_response


async def get_feeder_response(network, tx):
    """Execute transaction and return response."""
    gateway_url = get_feeder_url(network)
    gateway_client = FeederGatewayClient(url=gateway_url)
    gateway_response = await gateway_client.call_contract(invoke_tx=tx)

    return gateway_response["result"]


def get_gateway_url(network):
    """Return gateway URL for specified network"""
    if network == "localhost":
        return GATEWAYS.get(network)
    else:
        network = "alpha-" + network
        return f"https://{NETWORKS[network]}/gateway"


def get_feeder_url(network):
    """Return feeder gateway URL for specified network"""
    if network == "localhost":
        return GATEWAYS.get(network)
    else:
        network = "alpha-" + network
        return f"https://{NETWORKS[network]}/feeder_gateway"


def parse_information(x):
    """Extract information from deploy/declare command."""
    # address is 64, tx_hash is 64 chars long
    address, tx_hash = re.findall("0x[\\da-f]{1,64}", str(x))
    return address, tx_hash


def stringify(x):
    """Recursively convert list elements to strings."""
    if isinstance(x, list) or isinstance(x, tuple):
        return [stringify(y) for y in x]
    else:
        return str(x)


def prepare_params(params):
    """Sanitize call, invoke, and deploy parameters."""
    if params is None:
        params = []
    return stringify(params)


def prepare_return(x):
    """Unpack list and convert hex to integer."""
    for y in x:
        return int(y, 16)
