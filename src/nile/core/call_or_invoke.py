"""Command to call or invoke StarkNet smart contracts."""
import logging
import os
import subprocess

from nile import deployments
from nile.common import GATEWAYS, prepare_params
from starkware.starknet.services.api.gateway.transaction import InvokeFunction
from starkware.starknet.services.api.contract_class import ContractClass
from starkware.starknet.definitions import constants
from starkware.starknet.services.api.gateway.gateway_client import GatewayClient
from starkware.starkware_utils.error_handling import StarkErrorCode
from starkware.starknet.public.abi import get_selector_from_name



async def call_or_invoke(
    contract, type, method, params, network, signature=None, max_fee=None, token=None
):
    """Call or invoke functions of StarkNet smart contracts."""
    address, abi = next(deployments.load(contract, network))

    if max_fee is None:
        max_fee = 0

    tx = InvokeFunction(
        contract_address=int(address, 16),
        entry_point_selector=get_selector_from_name(method),
        calldata=prep(params),
        max_fee=max_fee,
        signature=prep(signature),
        version=constants.TRANSACTION_VERSION,
    )

    return await get_gateway_response(network, tx, token, type)


def prep(x):
    if isinstance(x, list) or isinstance(x, tuple):
        return [int(y) for y in x]
    else:
        return []

def prepare_return(x):
    return [int(y, 16) for y in x] if len(x) is not 0 else ""


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
