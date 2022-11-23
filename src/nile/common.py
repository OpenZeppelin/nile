"""nile common module."""
import json
import os
import re

from starkware.crypto.signature.fast_pedersen_hash import pedersen_hash
from starkware.starknet.core.os.class_hash import compute_class_hash
from starkware.starknet.services.api.contract_class import ContractClass

from nile.utils import normalize_number, str_to_felt

pt = os.path.dirname(os.path.realpath(__file__)).replace("/core", "")
CONTRACTS_DIRECTORY = "contracts"
BUILD_DIRECTORY = "artifacts"
TEMP_DIRECTORY = ".temp"
ABIS_DIRECTORY = f"{BUILD_DIRECTORY}/abis"
DEPLOYMENTS_FILENAME = "deployments.txt"
DECLARATIONS_FILENAME = "declarations.txt"
ACCOUNTS_FILENAME = "accounts.json"
NODE_FILENAME = "node.json"
RETRY_AFTER_SECONDS = 30
TRANSACTION_VERSION = 1
QUERY_VERSION_BASE = 2**128
QUERY_VERSION = QUERY_VERSION_BASE + TRANSACTION_VERSION
ETH_TOKEN_ABI = f"{pt}/artifacts/abis/ERC20.json"
ETH_TOKEN_ADDRESS = "0x49D36570D4E46F48E99674BD3FCC84644DDD6B96F7C741B1562B82F9E004DC7"
UNIVERSAL_DEPLOYER_ADDRESS = (
    # subject to change
    "0x041a78e741e5af2fec34b695679bc6891742439f7afb8484ecd7766661ad02bf"
)


def get_gateways():
    """Get the StarkNet node details."""
    try:
        with open(NODE_FILENAME, "r") as f:
            gateway = json.load(f)
            return gateway

    except FileNotFoundError:
        with open(NODE_FILENAME, "w") as f:
            networks = {
                "localhost": "http://127.0.0.1:5050/",
                "goerli2": "https://alpha4-2.starknet.io",
                "integration": "https://external.integration.starknet.io",
            }
            f.write(json.dumps(networks, indent=2))

            return networks


GATEWAYS = get_gateways()


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


def parse_information(x):
    """Extract information from deploy/declare command."""
    # address is 64, tx_hash is 64 chars long
    address, tx_hash = re.findall("0x[\\da-f]{1,64}", str(x))
    return normalize_number(address), normalize_number(tx_hash)


def stringify(x, process_short_strings=False):
    """Recursively convert list or tuple elements to strings."""
    if isinstance(x, list) or isinstance(x, tuple):
        return [stringify(y, process_short_strings) for y in x]
    else:
        if process_short_strings and is_string(x):
            return str(str_to_felt(x))
        return str(x)


def prepare_params(params):
    """Sanitize call, invoke, and deploy parameters."""
    if params is None:
        params = []
    return stringify(params, True)


def is_string(param):
    """Identify a param as string if is not int or hex."""
    is_int = True
    is_hex = True

    # convert to integer
    try:
        int(param)
    except Exception:
        is_int = False

    # convert to hex (starting with 0x)
    try:
        assert param.startswith("0x")
        int(param, 16)
    except Exception:
        is_hex = False

    return not is_int and not is_hex


def is_alias(param):
    """Identify param as alias (instead of address)."""
    return is_string(param)


def get_contract_class(contract_name, overriding_path=None):
    """Return the contract_class for a given contract name."""
    base_path = (
        overriding_path if overriding_path else (BUILD_DIRECTORY, ABIS_DIRECTORY)
    )
    with open(f"{base_path[0]}/{contract_name}.json", "r") as fp:
        contract_class = ContractClass.loads(fp.read())

    return contract_class


def get_class_hash(contract_name, overriding_path=None):
    """Return the class_hash for a given contract name."""
    contract_class = get_contract_class(contract_name, overriding_path)
    return compute_class_hash(contract_class=contract_class, hash_func=pedersen_hash)


def get_account_class_hash(contract="Account"):
    """Return the class_hash of an Account contract."""
    pt = os.path.dirname(os.path.realpath(__file__)).replace("/core", "")
    overriding_path = (f"{pt}/artifacts", f"{pt}/artifacts/abis")
    return get_class_hash(contract, overriding_path=overriding_path)


def get_addresses_from_string(string):
    """Return a set of integers with identified addresses in a string."""
    return set(
        int(address, 16) for address in re.findall("0x[\\da-f]{1,64}", str(string))
    )
