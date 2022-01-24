"""nile common module."""
import json
import os

CONTRACTS_DIRECTORY = "contracts"
BUILD_DIRECTORY = "artifacts"
TEMP_DIRECTORY = ".temp"
ABIS_DIRECTORY = f"{BUILD_DIRECTORY}/abis"
DEPLOYMENTS_FILENAME = "deployments.txt"
ACCOUNTS_FILENAME = "accounts.json"
NODE_FILENAME = "node.json"


def _get_gateway():
    """Get the StarkNet node details."""
    try:
        with open(NODE_FILENAME, "r") as f:
            gateway = json.load(f)
            return gateway

    except FileNotFoundError:
        with open(NODE_FILENAME, "w") as f:
            f.write('{"localhost": "http://localhost:5000/"}')


GATEWAYS = _get_gateway()


def get_all_contracts(ext=None):
    """Get all cairo contracts in the default contract directory."""
    if ext is None:
        ext = ".cairo"

    files = list()
    for (dirpath, _, filenames) in os.walk(CONTRACTS_DIRECTORY):
        files += [
            os.path.join(dirpath, file) for file in filenames if file.endswith(ext)
        ]

    return files
