"""Tests for declare command."""
import logging
from unittest.mock import AsyncMock, patch

import pytest

from nile.common import ABIS_DIRECTORY, BUILD_DIRECTORY, DECLARATIONS_FILENAME, set_args
from nile.core.declare import alias_exists, declare
from nile.utils import hex_address


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


SENDER = "0x1234"
CONTRACT = "contract"
SIGNATURE = ["123", "456"]
NETWORK = "localhost"
ALIAS = "alias"
PATH = (BUILD_DIRECTORY, ABIS_DIRECTORY)
OVERRIDING_PATH = ("new_path", ABIS_DIRECTORY)
MAX_FEE = "432"
CALL_OUTPUT = b"output"
HASH = 111
TX_HASH = 222


def test_alias_exists():
    # when alias does not exist
    assert alias_exists(ALIAS, NETWORK) is False

    # when alias exists
    with patch("nile.core.declare.deployments.load_class") as mock_load:
        mock_load.__iter__.side_effect = HASH
        assert alias_exists(ALIAS, NETWORK) is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, exp_command, exp_register",
    [
        (
            [SENDER, CONTRACT, SIGNATURE, NETWORK],  # args
            [  # expected command
                "--contract",
                f"{PATH[0]}/{CONTRACT}.json",
                "--signature",
                *SIGNATURE,
                "--max_fee",
                "0",
                "--sender",
                hex_address(SENDER),
            ],
            [HASH, NETWORK, None],  # expected register
        ),
        (
            [SENDER, CONTRACT, SIGNATURE, NETWORK, ALIAS],  # args
            [  # expected command
                "--contract",
                f"{PATH[0]}/{CONTRACT}.json",
                "--signature",
                *SIGNATURE,
                "--max_fee",
                "0",
                "--sender",
                hex_address(SENDER),
            ],
            [HASH, NETWORK, ALIAS],  # expected register
        ),
        (
            [SENDER, CONTRACT, SIGNATURE, NETWORK, ALIAS, OVERRIDING_PATH],  # args
            [  # expected command
                "--contract",
                f"{OVERRIDING_PATH[0]}/{CONTRACT}.json",
                "--signature",
                *SIGNATURE,
                "--max_fee",
                "0",
                "--sender",
                hex_address(SENDER),
            ],
            [HASH, NETWORK, ALIAS],  # expected register
        ),
        (
            [SENDER, CONTRACT, SIGNATURE, NETWORK, ALIAS, PATH, MAX_FEE],  # args
            [  # expected command
                "--contract",
                f"{PATH[0]}/{CONTRACT}.json",
                "--signature",
                *SIGNATURE,
                "--max_fee",
                MAX_FEE,
                "--sender",
                hex_address(SENDER),
            ],
            [HASH, NETWORK, ALIAS],  # expected register
        ),
    ],
)
@patch("nile.core.declare.parse_information", return_value=[HASH, TX_HASH])
@patch("nile.core.declare.deployments.register_class_hash")
async def test_declare(
    mock_register,
    mock_parse,
    caplog,
    args,
    exp_command,
    exp_register,
):
    logging.getLogger().setLevel(logging.INFO)
    with patch("nile.core.declare.call_cli", new=AsyncMock()) as mock_cli_call:
        mock_cli_call.return_value = CALL_OUTPUT
        # check return value
        res = await declare(*args)
        assert res == HASH

        # check internals
        args = set_args(NETWORK)

        mock_cli_call.assert_called_once_with("declare", args, exp_command)
        mock_parse.assert_called_once_with(CALL_OUTPUT)
        mock_register.assert_called_once_with(*exp_register)

        # check logs
        assert f"🚀 Declaring {CONTRACT}" in caplog.text
        assert (
            f"⏳ Successfully sent declaration of {CONTRACT} as {hex(HASH)}"
            in caplog.text
        )
        assert f"🧾 Transaction hash: {hex(TX_HASH)}" in caplog.text


@pytest.mark.asyncio
@patch("nile.core.declare.alias_exists", return_value=True)
async def test_declare_duplicate_hash(mock_alias_check):
    with pytest.raises(Exception) as err:
        await declare(ALIAS, NETWORK)

        assert (
            f"Alias {ALIAS} already exists in {NETWORK}.{DECLARATIONS_FILENAME}"
            in str(err.value)
        )
