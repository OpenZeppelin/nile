"""nile common module."""
import os
import re

CONTRACTS_DIRECTORY = "contracts"
BUILD_DIRECTORY = "artifacts"
TEMP_DIRECTORY = ".temp"
ABIS_DIRECTORY = f"{BUILD_DIRECTORY}/abis"
DEPLOYMENTS_FILENAME = "deployments.txt"

GATEWAYS = {"localhost": "http://localhost:5000/"}


def get_all_contracts(ext=None):
    """Get all cairo contracts in the default contract directory."""
    if ext is None:
        ext = ".cairo"

    files = list()
    for (dirpath, _, filenames) in os.walk(CONTRACTS_DIRECTORY):
        files += [os.path.join(dirpath, file) for file in filenames]

    return filter(lambda file: file.endswith(ext), files)


def get_address_from(x):
    """Extract an address from a string if exists."""
    return re.findall("0x[\\da-f]{64}", str(x))[0]
