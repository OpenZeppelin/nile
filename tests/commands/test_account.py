"""Tests for account commands."""
import logging
from unittest.mock import MagicMock, Mock, patch

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
async def test_account_multiple_inits_with_same_key():
    account = await Account(KEY, NETWORK)
    await account.deploy()
    account2 = await Account(KEY, NETWORK)

    # Check addresses don't match
    assert account.address != account2.address
    # Check indexing
    assert account.index == 0
    assert account2.index == 1


@pytest.mark.asyncio
async def test_deploy():
    account = await Account(KEY, NETWORK)
    with patch("nile.core.account.deploy", new=AsyncMock()) as mock_deploy:
        mock_deploy.return_value = (1, 2)
        with patch("nile.core.account.os.path.dirname") as mock_path:
            test_path = "/overriding_path"
            mock_path.return_value.replace.return_value = test_path

            await account.deploy()

            mock_deploy.assert_called_with(
                alias=f"account-{account.index + 1}",
                arguments=[str(account.signer.public_key)],
                contract_name="Account",
                network=NETWORK,
                overriding_path=(
                    f"{test_path}/artifacts",
                    f"{test_path}/artifacts/abis",
                ),
            )


@pytest.mark.asyncio
async def test_deploy_accounts_register():
    with patch("nile.core.account.deploy", new=AsyncMock()) as mock_deploy:
        with patch("nile.core.account.accounts.register") as mock_register:
            mock_deploy.return_value = (MOCK_ADDRESS, MOCK_INDEX)
            account = await Account(KEY, NETWORK)

            mock_register.assert_called_once_with(
                account.signer.public_key, MOCK_ADDRESS, MOCK_INDEX, NETWORK
            )


@pytest.mark.asyncio
async def test_send_nonce_call():
    account = await Account(KEY, NETWORK)
    contract_address, _ = await account.deploy()
    with patch("nile.core.account.Account.get_nonce", new=AsyncMock()) as mock_nonce:

        # Instead of creating and populating a tmp .txt file, this uses the
        # deployed account address (contract_address) as the target
        mock_nonce.return_value = 1
        await account.send(
            to=contract_address, method="method", calldata=[1, 2, 3], max_fee=1
        )

        # Check 'get_nonce' call
        mock_nonce.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "callarray, calldata",
    # The following callarray and calldata args tests the Account's list comprehensions
    # ensuring they're set to strings and passed correctly
    [([[111]], []), ([[111, 222]], [333, 444, 555])],
)
async def test_send_sign_transaction_and_execute(callarray, calldata):
    account = await Account(KEY, NETWORK)
    contract_address, _ = await account.deploy()

    sig_r, sig_s = [999, 888]
    return_signature = [callarray, calldata, sig_r, sig_s]

    account.signer.sign_transaction = MagicMock(return_value=return_signature)

    with patch("nile.core.account.call_or_invoke", new=AsyncMock()) as mock_call:
        send_args = [contract_address, "method", [1, 2, 3]]
        nonce = 4
        max_fee = 1
        await account.send(*send_args, max_fee, nonce)

        # Check values are correctly passed to 'sign_transaction'
        account.signer.sign_transaction.assert_called_once_with(
            calls=[send_args], nonce=nonce, sender=account.address, max_fee=1
        )

        # Check values are correctly passed to '__execute__'
        mock_call.assert_called_with(
            contract=account.address,
            max_fee=max_fee,
            method="__execute__",
            network=NETWORK,
            params=[
                len(callarray),
                *(elem for sublist in callarray for elem in sublist),
                len(calldata),
                *(param for param in calldata),
                nonce,
            ],
            signature=[sig_r, sig_s],
            type="invoke",
        )


@pytest.mark.asyncio
async def test_nonce_call():
    account = await Account(KEY, NETWORK)
    with patch("nile.core.account.call_or_invoke", new=AsyncMock()) as mock_call:
        await account.get_nonce()

        mock_call.assert_called_once_with(
            contract=account.address,
            type="call",
            method="get_nonce",
            params=[],
            network=account.network,
        )
