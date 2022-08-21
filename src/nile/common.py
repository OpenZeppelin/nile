"""nile common module."""
import json
import os
import re
import subprocess
from starkware.starknet.services.api.gateway.gateway_client import GatewayClient
from starkware.starkware_utils.error_handling import StarkErrorCode
from starkware.starknet.cli.starknet_cli import parse_hex_arg



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


async def get_gateway_response(network, tx, token, type):
    gateway_client = GatewayClient(url=GATEWAYS.get(network))
    gateway_response = await gateway_client.add_transaction(tx=tx, token=token)

    if gateway_response["code"] != StarkErrorCode.TRANSACTION_RECEIVED.name:
        raise BaseException(
            f"Transaction failed because:\n{gateway_response}."
        )
    if type == "deploy" or type == "invoke":
        return gateway_response["address"], gateway_response["transaction_hash"]
    elif type == "declare":
        return gateway_response["class_hash"], gateway_response["transaction_hash"]
    elif type == "call":
        return prepare_return(gateway_response["result"])
    else:
        raise TypeError(f"Unknown type '{type}', must be 'deploy' or 'declare'")



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
    #return [int(y, 16) for y in x] if len(x) is not 0 else ""
    for y in x:
        return int(y, 16)
