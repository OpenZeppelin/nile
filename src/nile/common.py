"""nile common module."""
import os

CONTRACTS_DIRECTORY = "contracts/"
BUILD_DIRECTORY = "artifacts/"
TEMP_DIRECTORY = ".temp/"
ABIS_DIRECTORY = f"{BUILD_DIRECTORY}abis/"


def get_all_contracts(ext=None):
    """Get all cairo contracts in the default contract directory."""
    if ext is None:
        ext = ".cairo"

    listOfFiles = list()
    for (dirpath, dirnames, filenames) in os.walk(CONTRACTS_DIRECTORY):
        listOfFiles += [os.path.join(dirpath, file) for file in filenames]

    return filter(lambda file : file.endswith(ext), listOfFiles)
