"""nile constants."""
import os

CONTRACTS_DIRECTORY = "contracts/"
BUILD_DIRECTORY = "artifacts/"
TEMP_DIRECTORY = ".temp/"
ABIS_DIRECTORY = f"{BUILD_DIRECTORY}abis/"


def get_all_contracts(ext=None):
    """Get all cairo contracts in the default contract directory."""
    if ext is None:
        ext = ".cairo"
    for filename in os.listdir(CONTRACTS_DIRECTORY):
        if filename.endswith(ext):
            yield os.path.join(CONTRACTS_DIRECTORY, filename)
