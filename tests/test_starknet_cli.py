"""Tests for starknet_cli module."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starkware.starkware_utils.error_handling import StarkErrorCode

from nile.starknet_cli import (
    _add_args,
    capture_stdout,
    get_feeder_url,
    get_gateway_response,
    get_gateway_url,
    set_command_args,
    set_context,
)

NETWORK = "localhost"
INPUTS = ["1", "2"]
CONTRACT_NAME = "contract"
ADDRESS = "0x1234"
STDOUT_1 = "SDTOUT_1"
STDOUT_2 = "SDTOUT_2"

TX_RECEIVED = dict({"code": StarkErrorCode.TRANSACTION_RECEIVED.name, "result": "test"})
TX_FAILED = dict({"code": "test"})


@pytest.mark.parametrize(
    "network, url",
    [
        ("localhost", "http://127.0.0.1:5050/"),
        ("goerli", "https://alpha4.starknet.io/"),
        ("mainnet", "https://alpha-mainnet.starknet.io/"),
    ],
)
def test_set_context(network, url):
    args = set_context(network)
    _dict = {
        "gateway_url": url + "gateway",
        "feeder_gateway_url": url + "feeder_gateway",
        "wallet": "",
        "network_id": network,
        "account_dir": None,
        "account": None,
    }

    # "localhost" does not add suffix
    if network == "localhost":
        _dict["gateway_url"] = url
        _dict["feeder_gateway_url"] = url

    expected = SimpleNamespace(**_dict)
    assert args == expected


@pytest.mark.parametrize(
    "args, expected",
    [
        (["k", "v1"], ["--k", "v1"]),
        (["k", ["v1", "v2"]], ["--k", "v1", "v2"]),
        (["k", ["v1", "v2", ["v3", ["v4"]]]], ["--k", "v1", "v2", "v3", "v4"]),
    ],
)
def test__add_args(args, expected):
    result = _add_args(*args)
    assert result == expected


@pytest.mark.parametrize(
    "args, expected",
    [
        (
            {"address": ADDRESS, "inputs": INPUTS},
            ["--address", ADDRESS, "--inputs", "1", "2"],
        ),
        (
            {"inputs": INPUTS, "contract_name": CONTRACT_NAME},
            [
                "--contract",
                f"artifacts/{CONTRACT_NAME}.json",
                "--inputs",
                "1",
                "2",
            ],
        ),
        (
            {"method": "METHOD", "query_flag": "simulate"},
            ["--function", "METHOD", "--simulate"],
        ),
        (
            {"error_message": True, "arguments": INPUTS},
            ["--error_message", "1", "2"],
        ),
    ],
)
def test_set_command_args(args, expected):
    result = set_command_args(**args)
    assert result == expected


@pytest.mark.parametrize(
    "network, expected",
    [
        ("localhost", "http://127.0.0.1:5050/"),
        ("goerli", "https://alpha4.starknet.io/gateway"),
        ("mainnet", "https://alpha-mainnet.starknet.io/gateway"),
    ],
)
def test_get_gateway_url(network, expected):
    if network == "localhost":
        with patch("nile.starknet_cli.GATEWAYS") as mock_gateways:
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
    if network == "localhost":
        with patch("nile.starknet_cli.GATEWAYS") as mock_gateways:
            mock_gateways.get = MagicMock(return_value=expected)
            url = get_feeder_url(network)
            assert url == expected
    else:
        url = get_feeder_url(network)
        assert url == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "success, tx_response",
    [
        (False, TX_FAILED),
        (True, TX_RECEIVED),
    ],
)
@patch("nile.core.deploy.DeployAccount")
async def test_get_gateway_response(mock_tx, success, tx_response):
    with patch(
        "nile.starknet_cli.GatewayClient.add_transaction", new=AsyncMock()
    ) as mock_client:
        mock_client.return_value = tx_response
        args = dict({"network": NETWORK, "tx": mock_tx, "token": None})

        if success:
            # success
            res = await get_gateway_response(**args)
            assert res == tx_response

        else:
            mock_client.return_value = tx_response

            with pytest.raises(BaseException) as err:
                await get_gateway_response(**args)
            assert "Failed to send transaction. Response: {'code': 'test'}." in str(
                err.value
            )

        mock_client.assert_called_once_with(tx=mock_tx, token=None)


@pytest.mark.asyncio
async def test_capture_stdout():
    async def helper():
        print(STDOUT_1)
        print(STDOUT_2)

    output = await capture_stdout(helper())

    assert f"{STDOUT_1}\n{STDOUT_2}" in output
