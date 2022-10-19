"""Tests for declare command."""
import logging
from unittest.mock import Mock, patch

import pytest

from nile.common import DECLARATIONS_FILENAME
from nile.core.declare import alias_exists, declare


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


class AsyncMock(Mock):
    """Return asynchronous mock."""

    async def __call__(self, *args, **kwargs):
        """Return mocked coroutine."""
        return super(AsyncMock, self).__call__(*args, **kwargs)


CONTRACT = "contract"
NETWORK = "goerli"
ALIAS = "alias"
PATH = "path"
HASH = 111
TX_HASH = 222
RUN_OUTPUT = [HASH, TX_HASH]


def test_alias_exists():
    # when alias does not exist
    assert alias_exists(ALIAS, NETWORK) is False

    # when alias exists
    with patch("nile.core.declare.deployments.load_class") as mock_load:
        mock_load.__iter__.side_effect = HASH
        assert alias_exists(ALIAS, NETWORK) is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, exp_register",
    [
        (
            [CONTRACT, NETWORK],  # args
            [HASH, NETWORK, None],  # expected register
        ),
        (
            [CONTRACT, NETWORK, ALIAS],  # args
            [HASH, NETWORK, ALIAS],  # expected register
        ),
        (
            [CONTRACT, NETWORK, ALIAS, PATH],  # args
            [HASH, NETWORK, ALIAS],  # expected register
        ),
    ],
)
async def test_declare(caplog, args, exp_register):
    logging.getLogger().setLevel(logging.INFO)
    with patch("nile.core.declare.capture_stdout", new=AsyncMock()) as mock_capture:
        mock_capture.return_value = [HASH, TX_HASH]
        with patch("nile.core.declare.parse_information") as mock_parse:
            mock_parse.return_value = [HASH, TX_HASH]
            with patch("nile.core.declare.run_command", new=AsyncMock()):
                with patch("nile.core.declare.deployments.register_class_hash") as mock_register:
                    # check return value
                    res = await declare(*args)
                    assert res == HASH

                    # check internals
                    mock_parse.assert_called_once_with(RUN_OUTPUT)
                    mock_register.assert_called_once_with(*exp_register)

                    # check logs
                    assert f"🚀 Declaring {CONTRACT}" in caplog.text
                    assert (
                        f"⏳ Declaration of {CONTRACT} successfully sent at {hex(HASH)}" in caplog.text
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
