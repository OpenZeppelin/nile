"""Tests for account commands."""
import logging
from unittest.mock import ANY, Mock, MagicMock, patch

import pytest

from nile.core.account import Account

KEY = "TEST_KEY"
NETWORK = "goerli"
MOCK_ADDRESS = "0x123"
MOCK_INDEX = 0


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


class AsyncMock(Mock):
    """Return asynchronous mock."""

    async def __call__(self, *args, **kwargs):
        """Return mocked coroutine."""
        return super(AsyncMock, self).__call__(*args, **kwargs)


@pytest.mark.asyncio
async def test_account_init():
    with patch("nile.core.account.Account.deploy", new=AsyncMock()) as mock_deploy:
        mock_deploy.return_value = MOCK_ADDRESS, MOCK_INDEX
        account = await Account(KEY, NETWORK)

        assert account.address == MOCK_ADDRESS
        assert account.index == MOCK_INDEX
        mock_deploy.assert_called_once()


@pytest.mark.asyncio
async def test_account_init_bad_key(caplog):
    logging.getLogger().setLevel(logging.INFO)

    await Account("BAD_KEY", NETWORK)
    assert (
        "\n❌ Cannot find BAD_KEY in env."
        "\nCheck spelling and that it exists."
        "\nTry moving the .env to the root of your project."
    ) in caplog.text


@pytest.mark.asyncio
async def test_deploy():
    with patch("nile.core.account.deploy", new=AsyncMock()) as mock_deploy:
        mock_deploy.return_value = (1, 2)
        with patch("nile.core.account.os.path.dirname") as mock_path:
            test_path = "/overriding_path"
            mock_path.return_value.replace.return_value = test_path

            account = await Account(KEY, NETWORK)

            expected = [
                "Account",                          # contract
                [account.signer.public_key],        # arguments
                NETWORK,                            # network
                f"account-{account.index}",         # alias
                (
                    f"{test_path}/artifacts",       # overriding-
                    f"{test_path}/artifacts/abis",  # path
                ),
            ]

            mock_deploy.assert_called_with(*expected)


@pytest.mark.asyncio
async def test_deploy_accounts_register():
    with patch("nile.core.account.deploy", new=AsyncMock()) as mock_deploy:
        with patch("nile.core.account.accounts.register") as mock_register:
            mock_deploy.return_value = (MOCK_ADDRESS, MOCK_INDEX)
            account = await Account(KEY, NETWORK)

            mock_register.assert_called_once_with(
                account.signer.public_key, MOCK_ADDRESS, MOCK_INDEX, KEY, NETWORK
            )


@pytest.mark.asyncio
async def test_send_sign_transaction_and_execute():
    account = await Account(KEY, NETWORK)

    calldata = ["111", "222", "333"]
    sig_r, sig_s = [999, 888]
    return_signature = [calldata, sig_r, sig_s]

    account.signer.sign_transaction = MagicMock(return_value=return_signature)

    with patch("nile.core.account.call_or_invoke", new=AsyncMock()) as mock_call:
        send_args = [account.address, "method", [1, 2, 3]]
        nonce = 4
        max_fee = 1
        await account.send(*send_args, max_fee, nonce)

        # Check values are correctly passed to 'sign_transaction'
        account.signer.sign_transaction.assert_called_once_with(
            calls=[send_args], nonce=nonce, sender=account.address, max_fee=1
        )

        # Check values are correctly passed to '__execute__'
        mock_call.assert_called_with(
            contract=account,
            max_fee=str(max_fee),
            method="__execute__",
            network=NETWORK,
            params=calldata,
            signature=[str(sig_r), str(sig_s)],
            type="invoke",
        )
