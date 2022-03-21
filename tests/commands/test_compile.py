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
    mock__compile_contract.assert_called_once_with(CONTRACT, CONTRACTS_DIRECTORY, False)


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


def test__compile_contract(mock_subprocess):
    contract_name_root = "contract"
    path = f"path/to/{contract_name_root}.cairo"

    mock_process = Mock()
    mock_subprocess.Popen.return_value = mock_process

    _compile_contract(path)

    mock_subprocess.Popen.assert_called_once_with(
        [
            "starknet-compile",
            path,
            f"--cairo_path={CONTRACTS_DIRECTORY}",
            "--output",
            f"artifacts/{contract_name_root}.json",
            "--abi",
            f"artifacts/abis/{contract_name_root}.json",
        ],
        stdout=mock_subprocess.PIPE,
    )
    mock_process.communicate.assert_called_once()


def test__compile_account_contract(mock_subprocess):
    contract_name_root = "mock_account"
    path = f"path/to/{contract_name_root}.cairo"

    mock_process = Mock()
    mock_subprocess.Popen.return_value = mock_process

    _compile_contract(path, account_contract="--account_contract")

    mock_subprocess.Popen.assert_called_once_with(
        [
            "starknet-compile",
            path,
            f"--cairo_path={CONTRACTS_DIRECTORY}",
            "--output",
            f"artifacts/{contract_name_root}.json",
            "--abi",
            f"artifacts/abis/{contract_name_root}.json",
            "--account_contract",
        ],
        stdout=mock_subprocess.PIPE,
    )
    mock_process.communicate.assert_called_once()
