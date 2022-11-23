"""Tests for account commands."""
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nile.common import (
    ABIS_DIRECTORY,
    BUILD_DIRECTORY,
    QUERY_VERSION,
    TRANSACTION_VERSION,
    UNIVERSAL_DEPLOYER_ADDRESS,
)
from nile.core.account import Account
from nile.utils import normalize_number

KEY = "TEST_KEY"
NETWORK = "localhost"
MOCK_ADDRESS = 0x123
MOCK_TARGET_ADDRESS = 0x987
MOCK_INDEX = 0
MAX_FEE = 10
SALT = 444
SIGNATURE = [111, 222]
CLASS_HASH = 12345


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.mark.asyncio
@patch("nile.core.account.Account.deploy", return_value=(MOCK_ADDRESS, MOCK_INDEX))
async def test_account_init(mock_deploy):
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
@patch("nile.core.account.deploy_account", return_value=(1, 2))
@patch("nile.common.get_class_hash", return_value=CLASS_HASH)
@patch("nile.core.account.Signer.sign_deployment", return_value=SIGNATURE)
@patch("nile.core.account.os.path.dirname")
async def test_deploy(mock_path, mock_signer, mock_hash, mock_deploy):
    test_path = "/overriding_path"
    overriding_path = (
        f"{test_path}/artifacts",
        f"{test_path}/artifacts/abis",
    )

    mock_path.return_value.replace.return_value = test_path

    account = await Account(KEY, NETWORK, salt=SALT, max_fee=MAX_FEE)
    calldata = [account.signer.public_key]

    mock_deploy.assert_called_with(
        network=NETWORK,
        salt=SALT,
        calldata=calldata,
        signature=SIGNATURE,
        max_fee=MAX_FEE,
        query_type=None,
        overriding_path=overriding_path,
        watch_mode=None,
    )


@pytest.mark.asyncio
@patch("nile.core.account.deploy_account", return_value=(MOCK_ADDRESS, MOCK_INDEX))
@patch("nile.core.account.get_account_class_hash", return_value=CLASS_HASH)
@patch("nile.core.account.accounts.register")
async def test_deploy_accounts_register(mock_register, mock_hash, mock_deploy):
    account = await Account(KEY, NETWORK)

    mock_register.assert_called_once_with(
        account.signer.public_key, MOCK_ADDRESS, MOCK_INDEX, KEY, NETWORK
    )


@pytest.mark.asyncio
@patch("nile.core.account.deploy_account", return_value=(MOCK_ADDRESS, MOCK_INDEX))
@patch("nile.core.account.get_account_class_hash", return_value=CLASS_HASH)
@patch("nile.core.account.get_contract_class", return_value="ContractClass")
@patch("nile.core.account.declare")
async def test_declare(mock_declare, mock_get_class, mock_hash, mock_deploy):
    account = await Account(KEY, NETWORK)

    signature = [999, 888]
    nonce = 4
    max_fee = 1
    contract_name = "contract"
    alias = "my_contract"
    overriding_path = (BUILD_DIRECTORY, ABIS_DIRECTORY)

    account.signer.sign_declare = MagicMock(return_value=signature)

    await account.declare(
        contract_name,
        max_fee=max_fee,
        nonce=nonce,
        alias=alias,
        overriding_path=overriding_path,
    )

    # Check 'get_contract_class' call
    mock_get_class.assert_called_once_with(
        contract_name=contract_name, overriding_path=overriding_path
    )

    # Check values are correctly passed to 'sign_declare'
    account.signer.sign_declare.assert_called_once_with(
        sender=account.address,
        contract_class="ContractClass",
        nonce=nonce,
        max_fee=max_fee,
    )

    # Check values are correctly passed to 'core.declare'
    mock_declare.assert_called_with(
        sender=account.address,
        contract_name=contract_name,
        signature=signature,
        network=NETWORK,
        alias=alias,
        max_fee=max_fee,
        mainnet_token=None,
        watch_mode=None,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("deployer_address", [None, 0xDE0])
@pytest.mark.parametrize("watch_mode", [None, "debug"])
@pytest.mark.parametrize("abi", [None, "TEST_ABI"])
@patch("nile.core.account.deploy_account", return_value=(MOCK_ADDRESS, MOCK_INDEX))
@patch("nile.core.deploy.get_class_hash", return_value=0x434343)
@patch("nile.core.account.deploy_with_deployer")
async def test_deploy_contract(
    mock_deploy_contract, mock_get_class, mock_deploy, abi, watch_mode, deployer_address
):
    account = await Account(KEY, NETWORK)

    contract_name = "contract"
    salt = 4
    unique = True
    calldata = []
    alias = "my_contract"
    max_fee = 1

    await account.deploy_contract(
        contract_name,
        salt,
        unique,
        calldata,
        alias,
        max_fee,
        deployer_address,
        abi,
        watch_mode,
    )

    if deployer_address is None:
        deployer_address = normalize_number(UNIVERSAL_DEPLOYER_ADDRESS)

    # Check values are correctly passed to 'deploy_with_deployer'
    mock_deploy_contract.assert_called_with(
        account,
        contract_name,
        salt,
        unique,
        calldata,
        alias,
        deployer_address,
        max_fee,
        abi=abi,
        watch_mode=watch_mode,
    )


@pytest.mark.asyncio
@patch("nile.core.account.deploy_account", return_value=(MOCK_ADDRESS, MOCK_INDEX))
@patch("nile.core.account.get_account_class_hash", return_value=CLASS_HASH)
@patch("nile.core.account.get_nonce", return_value=0)
@patch("nile.core.account.call_or_invoke")
@patch(
    "nile.core.account.Account._get_target_address", return_value=MOCK_TARGET_ADDRESS
)
async def test_send_nonce_call(
    mock_target_address, mock_call, mock_nonce, mock_hash, mock_deploy
):
    account = await Account(KEY, NETWORK)

    await account.send(MOCK_TARGET_ADDRESS, "method", [1, 2, 3], max_fee=1)

    # 'call_or_invoke' is called once for '__execute__'
    assert mock_call.call_count == 1

    # Check 'get_nonce' call
    mock_nonce.assert_called_once_with(account.address, NETWORK)


@pytest.mark.asyncio
@patch("nile.core.account.deploy_account", return_value=(MOCK_ADDRESS, MOCK_INDEX))
@patch("nile.core.account.get_account_class_hash", return_value=CLASS_HASH)
@patch(
    "nile.core.account.Account._get_target_address", return_value=MOCK_TARGET_ADDRESS
)
async def test_send_sign_invoke_and_execute(
    mock_target_address, mock_hash, mock_deploy
):
    account = await Account(KEY, NETWORK)

    calldata = [111, 222, 333]
    sig_r, sig_s = SIGNATURE
    return_signature = [calldata, sig_r, sig_s]

    account.signer.sign_invoke = MagicMock(return_value=return_signature)

    with patch("nile.core.account.call_or_invoke") as mock_call:
        send_args = [MOCK_TARGET_ADDRESS, "method", [1, 2, 3]]
        nonce = 4
        max_fee = 1
        await account.send(*send_args, max_fee=max_fee, nonce=nonce)

        # Check values are correctly passed to 'sign_invoke'
        account.signer.sign_invoke.assert_called_once_with(
            calls=[send_args],
            nonce=nonce,
            sender=account.address,
            max_fee=1,
            version=TRANSACTION_VERSION,
        )

        # Check values are correctly passed to '__execute__'
        mock_call.assert_called_with(
            contract=account.address,
            max_fee=max_fee,
            method="__execute__",
            abi=account.abi_path,
            network=NETWORK,
            params=calldata,
            signature=[sig_r, sig_s],
            type="invoke",
            query_flag=None,
            watch_mode=None,
        )


@pytest.mark.asyncio
@patch("nile.core.account.deploy_account", return_value=(MOCK_ADDRESS, MOCK_INDEX))
@patch("nile.core.account.get_account_class_hash", return_value=CLASS_HASH)
@patch(
    "nile.core.account.Account._get_target_address", return_value=MOCK_TARGET_ADDRESS
)
@patch("nile.core.account.get_nonce", return_value=0)
@patch("nile.core.account.call_or_invoke")
async def test_send_defaults(
    mock_call, mock_nonce, mock_target_address, mock_hash, mock_deploy
):
    account = await Account(KEY, NETWORK)

    send_args = [MOCK_TARGET_ADDRESS, "method", [1, 2, 3]]
    calldata = [111, 222, 333]
    sig_r, sig_s = SIGNATURE
    return_signature = [calldata, sig_r, sig_s]

    # Mock sign_invoke
    account.signer.sign_invoke = MagicMock(return_value=return_signature)

    await account.send(account.address, "method", [1, 2, 3])

    account.signer.sign_invoke.assert_called_once_with(
        calls=[send_args],
        nonce=0,
        sender=account.address,
        max_fee=0,
        version=TRANSACTION_VERSION,
    )

    mock_call.assert_called_with(
        contract=account.address,
        max_fee=0,
        method="__execute__",
        abi=account.abi_path,
        network=NETWORK,
        params=calldata,
        signature=[sig_r, sig_s],
        type="invoke",
        query_flag=None,
        watch_mode=None,
    )


@pytest.mark.asyncio
@patch("nile.core.account.deploy_account", return_value=(MOCK_ADDRESS, MOCK_INDEX))
@patch("nile.core.account.get_account_class_hash", return_value=CLASS_HASH)
async def test_estimate_fee(mock_hash, mock_deploy):
    account = await Account(KEY, NETWORK)
    # Mock send
    account.send = AsyncMock()

    await account.estimate_fee(account.address, "method", [1, 2, 3])

    account.send.assert_called_once_with(
        account.address, "method", [1, 2, 3], None, None, "estimate_fee"
    )


@pytest.mark.asyncio
@patch("nile.core.account.deploy_account", return_value=(MOCK_ADDRESS, MOCK_INDEX))
@patch("nile.core.account.get_account_class_hash", return_value=CLASS_HASH)
async def test_simulate(mock_hash, mock_deploy):
    account = await Account(KEY, NETWORK)
    # Mock send
    account.send = AsyncMock()

    await account.simulate(account.address, "method", [1, 2, 3])

    account.send.assert_called_once_with(
        account.address, "method", [1, 2, 3], None, None, "simulate"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("query_type", ["estimate_fee", "simulate"])
@pytest.mark.parametrize("watch_mode", ["track", "debug"])
@patch("nile.core.account.deploy_account", return_value=(MOCK_ADDRESS, MOCK_INDEX))
@patch("nile.core.account.get_account_class_hash", return_value=CLASS_HASH)
@patch(
    "nile.core.account.Account._get_target_address", return_value=MOCK_TARGET_ADDRESS
)
@patch("nile.core.account.get_nonce", return_value=0)
@patch("nile.core.account.call_or_invoke")
async def test_execute_query(
    mock_call,
    mock_nonce,
    mock_target_address,
    mock_hash,
    mock_deploy,
    watch_mode,
    query_type,
):
    account = await Account(KEY, NETWORK)

    send_args = [MOCK_TARGET_ADDRESS, "method", [1, 2, 3]]
    calldata = [111, 222, 333]
    sig_r, sig_s = SIGNATURE
    return_signature = [calldata, sig_r, sig_s]

    # Mock sign_invoke
    account.signer.sign_invoke = MagicMock(return_value=return_signature)

    await account.send(
        account.address,
        "method",
        [1, 2, 3],
        max_fee=MAX_FEE,
        query_type=query_type,
        watch_mode=watch_mode,
    )

    account.signer.sign_invoke.assert_called_once_with(
        calls=[send_args],
        nonce=0,
        sender=account.address,
        max_fee=MAX_FEE,
        version=QUERY_VERSION,
    )

    # Check query_flag is correctly passed
    mock_call.assert_called_with(
        contract=account.address,
        max_fee=MAX_FEE,
        abi=account.abi_path,
        method="__execute__",
        network=NETWORK,
        params=calldata,
        signature=[sig_r, sig_s],
        type="invoke",
        query_flag=query_type,
        watch_mode=watch_mode,
    )
