"""Tests for declare command."""
import logging
from unittest.mock import patch

import pytest

from nile.common import DECLARATIONS_FILENAME
from nile.core.declare import alias_exists, declare


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


CONTRACT = "contract"
NETWORK = "goerli"
ALIAS = "alias"
PATH = "path"
RUN_OUTPUT = b"output"
HASH = 111
TX_HASH = 222


def test_alias_exists():
    # when alias does not exist
    assert alias_exists(ALIAS, NETWORK) is False

    # when alias exists
    with patch("nile.core.declare.deployments.load_class") as mock_load:
        mock_load.__iter__.side_effect = HASH
        assert alias_exists(ALIAS, NETWORK) is True


@pytest.mark.parametrize(
    "args, exp_command, exp_register",
    [
        (
            [CONTRACT, NETWORK],  # args
            [CONTRACT, NETWORK, None],  # expected command
            [HASH, NETWORK, None],  # expected register
        ),
        (
            [CONTRACT, NETWORK, ALIAS],  # args
            [CONTRACT, NETWORK, None],  # expected command
            [HASH, NETWORK, ALIAS],  # expected register
        ),
        (
            [CONTRACT, NETWORK, ALIAS, PATH],  # args
            [CONTRACT, NETWORK, PATH],  # expected command
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
    assert res == HASH

    # check internals
    mock_run_cmd.assert_called_once_with(*exp_command, operation="declare")
    mock_parse.assert_called_once_with(RUN_OUTPUT)
    mock_register.assert_called_once_with(*exp_register)

    # check logs
    assert f"🚀 Declaring {CONTRACT}" in caplog.text
    assert f"⏳ Declaration of {CONTRACT} successfully sent at {HASH}" in caplog.text
    assert f"🧾 Transaction hash: {TX_HASH}" in caplog.text


@patch("nile.core.declare.alias_exists", return_value=True)
def test_declare_duplicate_hash(mock_alias_check):

    with pytest.raises(Exception) as err:
        declare(ALIAS, NETWORK)

        assert (
            f"Alias {ALIAS} already exists in {NETWORK}.{DECLARATIONS_FILENAME}"
            in str(err.value)
        )
