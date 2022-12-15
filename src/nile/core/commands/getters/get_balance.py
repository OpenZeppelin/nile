"""Retrieve the Ether balance for a given address."""
from nile.common import ETH_TOKEN_ABI, ETH_TOKEN_ADDRESS
from nile.core.call_or_invoke import call_or_invoke
from nile.utils import from_uint, normalize_number


async def get_balance(account, network):
    """Get the Ether balance of an address."""
    output = await call_or_invoke(
        ETH_TOKEN_ADDRESS,
        "call",
        "balanceOf",
        [account],
        abi=ETH_TOKEN_ABI,
        network=network,
    )
    low, high = [normalize_number(felt) for felt in output.split()]
    return from_uint([low, high])
