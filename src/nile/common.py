"""nile common module."""
import json
import logging
import os
import re
import subprocess

CONTRACTS_DIRECTORY = "contracts"
BUILD_DIRECTORY = "artifacts"
TEMP_DIRECTORY = ".temp"
ABIS_DIRECTORY = f"{BUILD_DIRECTORY}/abis"
DEPLOYMENTS_FILENAME = "deployments.txt"
DECLARATIONS_FILENAME = "declarations.txt"
ACCOUNTS_FILENAME = "accounts.json"
NODE_FILENAME = "node.json"
RETRY_AFTER_SECONDS = 30
UNIVERSAL_DEPLOYER_ADDRESS = (
    "0x414aa016992e868fa22e21bd104757e280c83ecb260fe9bccd1caee2f7f590e"
)


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


def run_command(
    operation,
    network,
    contract_name=None,
    arguments=None,
    inputs=None,
    signature=None,
    max_fee=None,
    overriding_path=None,
):
    """Execute CLI command with given parameters."""
    command = ["starknet", operation]

    if contract_name is not None:
        base_path = (
            overriding_path if overriding_path else (BUILD_DIRECTORY, ABIS_DIRECTORY)
        )
        contract = f"{base_path[0]}/{contract_name}.json"
        command.append("--contract")
        command.append(contract)

    if inputs is not None:
        command.append("--inputs")
        command.extend(prepare_params(inputs))

    if signature is not None:
        command.append("--signature")
        command.extend(signature)

    if max_fee is not None:
        command.append("--max_fee")
        command.append(max_fee)

    if arguments is not None:
        command.extend(arguments)

    if network == "mainnet":
        os.environ["STARKNET_NETWORK"] = "alpha-mainnet"
    elif network == "goerli":
        os.environ["STARKNET_NETWORK"] = "alpha-goerli"
    else:
        command.append(f"--feeder_gateway_url={GATEWAYS.get(network)}")
        command.append(f"--gateway_url={GATEWAYS.get(network)}")

    command.append("--no_wallet")

    try:
        return subprocess.check_output(command).strip().decode("utf-8")
    except subprocess.CalledProcessError:
        p = subprocess.Popen(command, stderr=subprocess.PIPE)
        _, error = p.communicate()
        err_msg = error.decode()

        if "max_fee must be bigger than 0" in err_msg:
            logging.error(
                """
                \n😰 Whoops, looks like max fee is missing. Try with:\n
                --max_fee=`MAX_FEE`
                """
            )
        elif "transactions should go through the __execute__ entrypoint." in err_msg:
            logging.error(
                "\n\n😰 Whoops, looks like you're not using an account. Try with:\n"
                "\nnile send [OPTIONS] SIGNER CONTRACT_NAME METHOD [PARAMS]"
            )

        return ""


def get_nonce(contract_address, network):
    """Get the current nonce for contract address in a given network."""
    command = ["starknet", "get_nonce", "--contract_address", contract_address]

    if network == "mainnet":
        os.environ["STARKNET_NETWORK"] = "alpha-mainnet"
    elif network == "goerli":
        os.environ["STARKNET_NETWORK"] = "alpha-goerli"
    else:
        command.append(f"--feeder_gateway_url={GATEWAYS.get(network)}")

    return int(subprocess.check_output(command).strip())


def parse_information(x):
    """Extract information from deploy/declare command."""
    # address is 64, tx_hash is 64 chars long
    address, tx_hash = re.findall("0x[\\da-f]{1,64}", str(x))
    return address, tx_hash


def stringify(x):
    """Recursively convert list or tuple elements to strings."""
    if isinstance(x, list) or isinstance(x, tuple):
        return [stringify(y) for y in x]
    else:
        return str(x)


def prepare_params(params):
    """Sanitize call, invoke, and deploy parameters."""
    if params is None:
        params = []
    return stringify(params)
