"""Tests for declare command."""
import logging
from unittest.mock import patch

import pytest

from nile.core.declare import declare


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


CONTRACT = "contract"
NETWORK = "goerli"
ALIAS = "alias"
PATH = "path"
RUN_OUTPUT = b'output'
HASH = 111
TX_HASH = 222


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
