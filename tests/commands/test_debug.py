"""Tests for debug command."""
import logging
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from nile.common import BUILD_DIRECTORY
from nile.utils.debug import _abi_to_build_path, debug

MOCK_HASH = "0x1234"
NETWORK = "goerli"
ERROR_MESSAGE = "Error at pc=0:1:\nAn ASSERT_EQ instruction failed: 3 != 0."


def mocked_json_message(arg):
    return {"tx_status": arg, "tx_failure_reason": {"error_message": ERROR_MESSAGE}}


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test__abi_to_build_path():
    Path(BUILD_DIRECTORY).mkdir()
    filename = "contract"
    assert f"{BUILD_DIRECTORY}/{filename}" == _abi_to_build_path(filename)


@pytest.mark.parametrize(
    "args, expected",
    [
        ("ACCEPTED", "No error in transaction"),
        ("REJECTED", "The transaction was rejected"),
        ("REJECTED", ERROR_MESSAGE),
    ],
)
@pytest.mark.xfail(
    sys.version_info >= (3, 10),
    reason="Issue in cairo-lang. "
    "See https://github.com/starkware-libs/cairo-lang/issues/27",
)
@patch("nile.utils.debug.json.loads")
def test_debug_feedback_with_message(mock_json, caplog, args, expected):
    logging.getLogger().setLevel(logging.INFO)
    mock_json.return_value = mocked_json_message(args)

    debug(MOCK_HASH, NETWORK)

    assert expected in caplog.text
