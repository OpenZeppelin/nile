"""
Tests for compile command.

Only unit tests for now. No contracts are actually compiled.
"""

import logging
from unittest.mock import Mock, patch

import pytest

from nile.common import ABIS_DIRECTORY, CONTRACTS_DIRECTORY
from nile.core.compile import _compile_contract, compile

CONTRACT = "foo.cairo"


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


# Mock `subprocess` for all tests in this module to avoid actually running any
# shell commands.
@pytest.fixture(autouse=True)
def mock_subprocess():
    with patch("nile.core.compile.subprocess") as mock_subprocess:
        yield mock_subprocess


def test_compile_create_abis_directory(tmp_working_dir):
    assert not (tmp_working_dir / ABIS_DIRECTORY).exists()
    compile([])
    assert (tmp_working_dir / ABIS_DIRECTORY).exists()


@patch("nile.core.compile.get_all_contracts")
def test_compile_get_all_contracts_called(mock_get_all_contracts):
    compile([])
    mock_get_all_contracts.assert_called_once()
    mock_get_all_contracts.reset_mock()

    compile([CONTRACT])
    mock_get_all_contracts.assert_not_called()


@patch("nile.core.compile._compile_contract")
def test_compile__compile_contract_called(mock__compile_contract):
    compile([CONTRACT])
    mock__compile_contract.assert_called_once_with(
        CONTRACT, CONTRACTS_DIRECTORY, None, False, False
    )


@patch("nile.core.compile._compile_contract")
def test_compile_failure_feedback(mock__compile_contract, caplog):
    # make logs visible to test
    logging.getLogger().setLevel(logging.INFO)

    mock__compile_contract.side_effect = [0]
    compile([CONTRACT])
    assert "Done" in caplog.text

    mock__compile_contract.side_effect = [1]
    compile([CONTRACT])
    assert "Failed" in caplog.text


@pytest.mark.parametrize(
    "is_acct, disable_hint",
    [
        (False, False),
        (True, False),
        (False, True),
        (True, True),
    ],
)
def test__compile_contract(mock_subprocess, is_acct, disable_hint):
    mock_process = Mock()
    mock_subprocess.Popen.return_value = mock_process

    contract_name = "contract"
    path = f"path/to/{contract_name}.cairo"

    _compile_contract(
        path=path, account_contract=is_acct, disable_hint_validation=disable_hint
    )

    expected = [
        "starknet-compile",
        path,
        f"--cairo_path={CONTRACTS_DIRECTORY}",
        "--output",
        f"artifacts/{contract_name}.json",
        "--abi",
        f"artifacts/abis/{contract_name}.json",
    ]

    if is_acct:
        expected.append("--account_contract")

    if disable_hint:
        expected.append("--disable_hint_validation")

    mock_subprocess.Popen.assert_called_once_with(
        expected,
        stdout=mock_subprocess.PIPE,
    )
    mock_process.communicate.assert_called_once()


@pytest.mark.parametrize(
    "contract_name, flag",
    [
        ("Account", "--account_contract"),
        ("mock_Account", "--account_contract"),
        ("Account_Manager", False),
    ],
)
def test__compile_auto_account_flag(mock_subprocess, contract_name, flag):
    path = f"path/to/{contract_name}.cairo"

    mock_process = Mock()
    mock_subprocess.Popen.return_value = mock_process

    _compile_contract(path)

    command = [
        "starknet-compile",
        path,
        f"--cairo_path={CONTRACTS_DIRECTORY}",
        "--output",
        f"artifacts/{contract_name}.json",
        "--abi",
        f"artifacts/abis/{contract_name}.json",
    ]

    if flag is not False:
        command.append(flag)

    mock_subprocess.Popen.assert_called_once_with(
        command,
        stdout=mock_subprocess.PIPE,
    )
    mock_process.communicate.assert_called_once()


@pytest.mark.parametrize(
    "contract_name, directory, cairo_path, expected_internal_cairo_path",
    [
        ("Contract1", "contracts", None, "contracts"),
        ("Contract3", "src", "contracts:src", "contracts:src"),
        ("Contract1", None, "src", "src"),
        ("Contract4", None, None, CONTRACTS_DIRECTORY),
    ],
)
def test__compile_cairo_path(
    mock_subprocess, contract_name, directory, cairo_path, expected_internal_cairo_path
):
    path = f"path/to/{contract_name}.cairo"

    mock_process = Mock()
    mock_subprocess.Popen.return_value = mock_process

    compile([path], directory=directory, cairo_path=cairo_path)

    command = [
        "starknet-compile",
        path,
        f"--cairo_path={expected_internal_cairo_path}",
        "--output",
        f"artifacts/{contract_name}.json",
        "--abi",
        f"artifacts/abis/{contract_name}.json",
    ]

    mock_subprocess.Popen.assert_called_once_with(
        command,
        stdout=mock_subprocess.PIPE,
    )
    mock_process.communicate.assert_called_once()
