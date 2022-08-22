"""Command to call or invoke StarkNet smart contracts."""

from starkware.starknet.definitions import constants
from starkware.starknet.public.abi import get_selector_from_name
from starkware.starknet.services.api.gateway.transaction import InvokeFunction
from starkware.starknet.utils.api_utils import cast_to_felts

from nile import deployments
from nile.common import get_gateway_response, prepare_return


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
        calldata=cast_to_felts(params or []),
        max_fee=int(max_fee),
        signature=cast_to_felts(signature or []),
        version=constants.TRANSACTION_VERSION,
    )

    response = await get_gateway_response(network, tx, token, type)

    if type == "invoke":
        addr, tx_hash = response
        return addr, tx_hash
    elif type == "call":
        result = prepare_return(response)
        return result
    else:
        raise TypeError(f"Unknown type '{type}', must be 'call' or 'invoke'")
