"""Retrieve the Ether balance for a given address."""
from nile.common import ETH_ABI, ETH_ADDRESS
from nile.core.call_or_invoke import call_or_invoke
from nile.utils import from_uint


async def get_balance(account, network):
    """Get the Ether balance of an address."""
    output = await call_or_invoke(
        ETH_ADDRESS, "call", "balanceOf", [account], abi=ETH_ABI, network=network
    )
    low, high = output.split()
    return from_uint([int(low, 16), int(high, 16)])
