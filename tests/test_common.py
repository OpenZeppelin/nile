"""Tests for common library."""
import pytest
from unittest.mock import MagicMock, patch

from nile.common import (
    capture_stdout,
    get_feeder_url,
    get_gateway_url,
    parse_information,
    prepare_params,
    stringify,
)

NETWORK = "goerli"
ARGS = ["1", "2", "3"]
LIST1 = [1, 2, 3]
LIST2 = [1, 2, 3, [4, 5, 6]]
LIST3 = [1, 2, 3, [4, 5, 6, [7, 8, 9]]]
STDOUT_1 = "SDTOUT_1"
STDOUT_2 = "SDTOUT_2"


@pytest.mark.parametrize(
    "args, expected",
    [
        ([], []),
        ([LIST1], [["1", "2", "3"]]),
        ([LIST2], [["1", "2", "3", ["4", "5", "6"]]]),
        ([LIST3], [["1", "2", "3", ["4", "5", "6", ["7", "8", "9"]]]]),
    ],
)
def test_stringify(args, expected):
    assert stringify(args) == expected


@pytest.mark.parametrize(
    "args, expected",
    [
        ([], []),
        ([LIST1], [["1", "2", "3"]]),
        (
            ["MyToken name", "MyToken symbol"],
            ["23977024514528806274181721445", "1571358278584159847990373933805420"],
        ),
        (["0xbad", 1234, "1234", "bad"], ["0xbad", "1234", "1234", "6447460"]),
    ],
)
def test_prepare_params(args, expected):
    assert prepare_params(args) == expected


@pytest.mark.parametrize(
    "network, expected",
    [
        ("localhost", "http://127.0.0.1:5050/"),
        ("goerli", "https://alpha4.starknet.io/gateway"),
        ("mainnet", "https://alpha-mainnet.starknet.io/gateway"),
    ],
)
def test_get_gateway_url(network, expected):
    if network is "localhost":
        with patch("nile.common.GATEWAYS") as mock_gateways:
            mock_gateways.get = MagicMock(return_value=expected)
            url = get_gateway_url(network)
            assert url == expected

    else:
        url = get_gateway_url(network)
        assert url == expected


@pytest.mark.parametrize(
    "network, expected",
    [
        ("localhost", "http://127.0.0.1:5050/"),
        ("goerli", "https://alpha4.starknet.io/feeder_gateway"),
        ("mainnet", "https://alpha-mainnet.starknet.io/feeder_gateway"),
    ],
)
def test_get_feeder_url(network, expected):
    if network is "localhost":
        with patch("nile.common.GATEWAYS") as mock_gateways:
            mock_gateways.get = MagicMock(return_value=expected)
            url = get_feeder_url(network)
            assert url == expected

    else:
        url = get_feeder_url(network)
        assert url == expected


@pytest.mark.asyncio
async def test_capture_stdout():
    async def helper():
        print(STDOUT_1)
        print(STDOUT_2)

    output = await capture_stdout(helper())

    assert f"{STDOUT_1}\n{STDOUT_2}" in output


def test_parse_information():
    a = format(1, "#066x")
    b = format(2, "#066x")
    target = f"Formatting 'a': {a}. Formatting 'b': {b}."

    _a, _b = parse_information(target)
    assert _a, _b == (a, b)
