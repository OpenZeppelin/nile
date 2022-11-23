"""Tests for get-nonce command."""
from unittest.mock import patch

import pytest

from nile.common import ETH_TOKEN_ABI, ETH_TOKEN_ADDRESS
from nile.utils.get_balance import get_balance

NETWORKS = ["mainnet", "goerli", "goerli2", "localhost"]
CONTRACTS = ["0x4d2", "1234", 1234]
EXPECTED_VALUES = [
    ("1000 0", 1000),
    ("0 0", 0),
    ("1234564321 5432124", 1848456012128035929902520326020686465121776865),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("contract_address", CONTRACTS)
@pytest.mark.parametrize("network", NETWORKS)
@pytest.mark.parametrize("mock_return", EXPECTED_VALUES)
async def test_get_balance(contract_address, network, mock_return):
    with patch(
        "nile.utils.get_balance.call_or_invoke", return_value=mock_return[0]
    ) as mock_call:
        res = await get_balance(contract_address, network)

        mock_call.assert_called_once_with(
            ETH_TOKEN_ADDRESS,
            "call",
            "balanceOf",
            [contract_address],
            abi=ETH_TOKEN_ABI,
            network=network,
        )

        assert res == mock_return[1]
