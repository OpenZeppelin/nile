"""Tests for declare command."""
import logging
from unittest.mock import patch

import pytest

from nile.common import DECLARATIONS_FILENAME
from nile.core.declare import alias_exists, declare
from nile.utils import hex_address, hex_class_hash


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


SENDER = "0x1234"
CONTRACT = "contract"
SIGNATURE = [123, 321]
NETWORK = "localhost"
ALIAS = "alias"
PATH = "path"
MAX_FEE = 432
RUN_OUTPUT = b"output"
HASH = 111
TX_HASH = 222


def test_alias_exists():
    # when alias does not exist
    assert alias_exists(ALIAS, NETWORK) is False

    # when alias exists
    with patch("nile.core.declare.deployments.load_class") as mock_load:
        mock_load.__iter__.side_effect = hex_class_hash(HASH)
        assert alias_exists(ALIAS, NETWORK) is True


@pytest.mark.parametrize(
    "args, exp_command, exp_register",
    [
        (
            [SENDER, CONTRACT, SIGNATURE, NETWORK],  # args
            {  # expected command
                "contract_name": CONTRACT,
                "signature": SIGNATURE,
                "network": NETWORK,
                "arguments": ["--sender", hex_address(SENDER)],
                "overriding_path": None,
                "max_fee": "0",
                "mainnet_token": None,
            },
            [HASH, NETWORK, None],  # expected register
        ),
        (
            [SENDER, CONTRACT, SIGNATURE, NETWORK, ALIAS],  # args
            {  # expected command
                "contract_name": CONTRACT,
                "signature": SIGNATURE,
                "network": NETWORK,
                "arguments": ["--sender", hex_address(SENDER)],
                "overriding_path": None,
                "max_fee": "0",
                "mainnet_token": None,
            },
            [HASH, NETWORK, ALIAS],  # expected register
        ),
        (
            [SENDER, CONTRACT, SIGNATURE, NETWORK, ALIAS, PATH],  # args
            {  # expected command
                "contract_name": CONTRACT,
                "signature": SIGNATURE,
                "network": NETWORK,
                "arguments": ["--sender", hex_address(SENDER)],
                "overriding_path": PATH,
                "max_fee": "0",
                "mainnet_token": None,
            },
            [HASH, NETWORK, ALIAS],  # expected register
        ),
        (
            [SENDER, CONTRACT, SIGNATURE, NETWORK, ALIAS, PATH, MAX_FEE],  # args
            {  # expected command
                "contract_name": CONTRACT,
                "signature": SIGNATURE,
                "network": NETWORK,
                "arguments": ["--sender", hex_address(SENDER)],
                "overriding_path": PATH,
                "max_fee": str(MAX_FEE),
                "mainnet_token": None,
            },
            [HASH, NETWORK, ALIAS],  # expected register
        ),
    ],
)
@patch("nile.core.declare.run_command", return_value=RUN_OUTPUT)
@patch("nile.core.declare.parse_information", return_value=[HASH, TX_HASH])
@patch("nile.core.declare.deployments.register_class_hash")
def test_declare(
    mock_register, mock_parse, mock_run_cmd, caplog, args, exp_command, exp_register
):
    logging.getLogger().setLevel(logging.INFO)

    # check return value
    res = declare(*args)
    assert res == hex_class_hash(HASH)

    # check internals
    mock_run_cmd.assert_called_once_with(operation="declare", **exp_command)
    mock_parse.assert_called_once_with(RUN_OUTPUT)
    mock_register.assert_called_once_with(*exp_register)

    # check logs
    assert f"🚀 Declaring {CONTRACT}" in caplog.text
    assert (
        f"⏳ Successfully sent declaration of {CONTRACT} as {hex_class_hash(HASH)}"
        in caplog.text
    )
    assert f"🧾 Transaction hash: {hex(TX_HASH)}" in caplog.text


@patch("nile.core.declare.alias_exists", return_value=True)
def test_declare_duplicate_hash(mock_alias_check):

    with pytest.raises(Exception) as err:
        declare(ALIAS, NETWORK)

        assert (
            f"Alias {ALIAS} already exists in {NETWORK}.{DECLARATIONS_FILENAME}"
            in str(err.value)
        )
