"""Tests for account commands."""
import logging
from unittest.mock import MagicMock, Mock, patch

import pytest

from nile.core.account import Account, get_or_create_account

KEY = "TEST_KEY"
NETWORK = "localhost"
MOCK_ADDRESS = "0x123"
MOCK_INDEX = 0


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


class AsyncMock(Mock):
    def __call__(self, *args, **kwargs):
        sup = super()

        async def coro():
            return sup.__call__(*args, **kwargs)

        return coro()


@pytest.mark.asyncio
async def test_account_create_account():
    with patch("nile.core.account.Account.deploy", new=AsyncMock()) as mock_deploy:
        await get_or_create_account(KEY, NETWORK)

        mock_deploy.assert_called_once()


@pytest.mark.asyncio
async def test_account_get_account():
    with patch("nile.core.account.accounts", return_value=False):
        with patch("nile.core.account.Account.deploy", new=AsyncMock()) as mock_deploy:

            account = await get_or_create_account(KEY, NETWORK)
            assert type(account) == Account
            mock_deploy.assert_not_called()
