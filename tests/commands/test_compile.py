"""
Tests for compile command.

Only unit tests for now. No contracts are actually compiled.
"""
from unittest.mock import Mock, patch

import pytest

from nile.common import ABIS_DIRECTORY, CONTRACTS_DIRECTORY
from nile.commands.compile import _compile_contract, compile_command

CONTRACT = "foo.cairo"


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


# Mock `subprocess` for all tests in this module to avoid actually running any
# shell commands.
@pytest.fixture(autouse=True)
def mock_subprocess():
    with patch("nile.commands.compile.subprocess") as mock_subprocess:
        yield mock_subprocess


def test_compile_command_create_abis_directory(tmp_working_dir):
    assert not (tmp_working_dir / ABIS_DIRECTORY).exists()
    compile_command([])
    assert (tmp_working_dir / ABIS_DIRECTORY).exists()


@patch("nile.commands.compile.get_all_contracts")
def test_compile_command_get_all_contracts_called(mock_get_all_contracts):
    compile_command([])
    mock_get_all_contracts.assert_called_once()
    mock_get_all_contracts.reset_mock()

    compile_command([CONTRACT])
    mock_get_all_contracts.assert_not_called()


@patch("nile.commands.compile._compile_contract")
def test_compile_command__compile_contract_called(mock__compile_contract):
    compile_command([CONTRACT])
    mock__compile_contract.assert_called_once_with(CONTRACT)


@patch("nile.commands.compile._compile_contract")
def test_compile_command_failure_feedback(mock__compile_contract, capsys):
    mock__compile_contract.side_effect = [0]
    compile_command([CONTRACT])
    assert "Done" in capsys.readouterr().out

    mock__compile_contract.side_effect = [1]
    compile_command([CONTRACT])
    assert "Failed" in capsys.readouterr().out


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
