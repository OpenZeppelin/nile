"""Tests for get-nonce command."""
import logging
import os
from unittest.mock import patch

import pytest

from nile.utils.get_nonce import get_nonce

GATEWAYS = {"localhost": "http://127.0.0.1:5050/"}


@pytest.mark.parametrize(
    "contract_address, network",
    [("0xffff", "localhost"), ("0xffff", "goerli"), ("0xffff", "mainnet")],
)
@patch("nile.core.node.subprocess.check_output")
@patch("nile.common.get_gateway", return_value=GATEWAYS)
def test_call_format(mock_gateway, mock_subprocess, contract_address, network):
    get_nonce(contract_address, network)

    command = ["starknet", "get_nonce", "--contract_address", contract_address]
    if network == "localhost":
        command.append("--feeder_gateway_url=http://127.0.0.1:5050/")
    else:
        assert os.getenv("STARKNET_NETWORK") == f"alpha-{network}"

    mock_subprocess.assert_called_once_with(command)


@patch("nile.core.node.subprocess.check_output", return_value="5")
@patch("nile.common.get_gateway", return_value=GATEWAYS)
def test_get_nonce(mock_gateway, mock_subprocess, caplog):
    logging.getLogger().setLevel(logging.INFO)

    # check return values
    nonce = get_nonce("0xffff", "localhost")
    assert nonce == 5

    # check logs
    assert "Current Nonce: 5" in caplog.text


@pytest.mark.parametrize(
    "contract_address",
    ["0x4d2", "1234", 1234],
)
@patch("nile.core.node.subprocess.check_output")
@patch("nile.common.get_gateway", return_value=GATEWAYS)
def test_contract_address_formats(mock_gateway, mock_subprocess, contract_address):
    get_nonce(contract_address, "goerli")

    command = ["starknet", "get_nonce", "--contract_address", "0x4d2"]

    mock_subprocess.assert_called_once_with(command)
