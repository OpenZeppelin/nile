"""Call the starknet_cli."""

import io
import re
import sys
from types import SimpleNamespace

from starkware.starknet.cli import starknet_cli
from starkware.starknet.cli.starknet_cli import NETWORKS, assert_tx_received
from starkware.starknet.services.api.gateway.gateway_client import GatewayClient

from nile.common import ABIS_DIRECTORY, BUILD_DIRECTORY, GATEWAYS, prepare_params

ARGS = [
    "abi",
    "address",
    "contracts",
    "contract_address",
    "hash",
    "mainnet_token",
    "sender",
]


async def execute_call(cmd_name, network, **kwargs):
    """Build and execute call to starknet_cli."""
    args = set_context(network)
    command_args = set_command_args(**kwargs)
    cmd = getattr(starknet_cli, cmd_name)
    return await capture_stdout(cmd(args=args, command_args=command_args))


async def get_gateway_response(network, tx, token):
    """Execute transaction and return response."""
    gateway_url = get_gateway_url(network)
    gateway_client = GatewayClient(url=gateway_url)
    gateway_response = await gateway_client.add_transaction(tx=tx, token=token)
    assert_tx_received(gateway_response)

    return gateway_response


async def capture_stdout(func):
    """Return the stdout during the passed function call."""
    stdout = sys.stdout
    sys.stdout = io.StringIO()
    await func
    output = sys.stdout.getvalue()
    sys.stdout = stdout
    result = output.rstrip()
    return result


def set_context(network):
    """Set context args for StarkNet CLI call."""
    args = {
        "gateway_url": get_gateway_url(network),
        "feeder_gateway_url": get_feeder_url(network),
        "wallet": "",
        "network_id": network,
        "account_dir": None,
        "account": None,
    }
    ret_obj = SimpleNamespace(**args)
    return ret_obj


def set_command_args(**kwargs):
    """Set command args for StarkNet CLI call."""
    command_args = []

    for arg in ARGS:
        if kwargs.get(arg):
            command_args += _add_args(arg, kwargs.get(arg))

    # The rest of the arguments require unique handling
    if kwargs.get("contract_name"):
        base_path = (
            kwargs.get("overriding_path")
            if kwargs.get("overriding_path")
            else (BUILD_DIRECTORY, ABIS_DIRECTORY)
        )
        contract = f"{base_path[0]}/{kwargs.get('contract_name')}.json"
        command_args.append("--contract")
        command_args.append(contract)

    if kwargs.get("inputs"):
        command_args.append("--inputs")
        command_args.extend(prepare_params(kwargs.get("inputs")))

    if kwargs.get("signature"):
        command_args.append("--signature")
        command_args.extend(prepare_params(kwargs.get("signature")))

    if kwargs.get("max_fee"):
        command_args.append("--max_fee")
        command_args.extend(prepare_params(kwargs.get("max_fee")))

    if kwargs.get("method"):
        command_args.append("--function")
        command_args.append(kwargs.get("method"))

    if kwargs.get("query_flag"):
        command_args.append(f"--{kwargs.get('query_flag')}")

    if kwargs.get("error_message"):
        command_args.append("--error_message")

    if kwargs.get("arguments"):
        command_args.extend(kwargs.get("arguments"))

    return command_args


def get_gateway_url(network):
    """Return gateway URL for specified network."""
    networks = ["localhost", "goerli2", "integration"]
    if network in networks:
        return GATEWAYS.get(network)
    else:
        network = "alpha-" + network
        return f"https://{NETWORKS[network]}/gateway"


def get_feeder_url(network):
    """Return feeder gateway URL for specified network."""
    networks = ["localhost", "goerli2", "integration"]
    if network in networks:
        return GATEWAYS.get(network)
    else:
        network = "alpha-" + network
        return f"https://{NETWORKS[network]}/feeder_gateway"


def _add_args(key, value):
    if type(value) is not list:
        return [f"--{key}", value]
    else:
        pattern = re.compile(r"\w+")
        flat_list = pattern.findall(str(value))
        return [f"--{key}", *flat_list]
