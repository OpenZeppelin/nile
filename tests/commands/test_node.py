"""Tests for node command."""
import logging
from unittest.mock import patch

import pytest

from nile.core.node import node

HOSTS = ["127.0.0.1", "goerli"]
PORTS = ["5050", "5001"]
LITE = "--lite-mode"


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.mark.parametrize(
    "args, host, port, mode",
    [
        ([], HOSTS[0], PORTS[0], None),
        ([HOSTS[1], PORTS[1]], HOSTS[1], PORTS[1], None),
        ([HOSTS[1], PORTS[1], LITE], HOSTS[1], PORTS[1], LITE),
    ],
)
@patch("nile.core.node.subprocess.check_call")
def test_node_call(mock_subprocess, args, host, port, mode):
    node(*args)

    command = ["starknet-devnet", "--host", host, "--port", port]
    if mode:
        command.append(mode)
    mock_subprocess.assert_called_once_with(command)


@patch("nile.core.node.subprocess.check_call")
def test_node_error(mock_subprocess, caplog):
    logging.getLogger().setLevel(logging.INFO)

    mock_subprocess.side_effect = FileNotFoundError

    node()
    assert (
        "\n\n😰 Could not find starknet-devnet, is it installed? Try with:\n"
        "    pip install starknet-devnet"
    ) in caplog.text
