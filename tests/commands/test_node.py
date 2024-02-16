"""Tests for node command."""

import logging
from unittest.mock import patch

import pytest

from nile.core.node import get_help_message, node

HOST = "127.0.0.1"
PORT = "5050"
SEED = "123"
HELP_OUTPUT = b"optional arguments:\n options"


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.mark.parametrize("host", [HOST])
@pytest.mark.parametrize("port", [PORT])
@pytest.mark.parametrize(
    "node_args",
    [
        None,
        ("--seed", SEED),
        ("--lite-mode"),
        ("--fork-network", "alpha-mainnet"),
        ("--fork-block", 4),
    ],
)
@patch("nile.core.node.subprocess.check_call")
def test_node_call(mock_subprocess, host, port, node_args):
    node(host, port, node_args)

    command = ["starknet-devnet", "--host", host, "--port", port]
    if node_args is not None:
        command += list(node_args)
    mock_subprocess.assert_called_once_with(command)


@patch("nile.core.node.subprocess.check_output", return_value=HELP_OUTPUT)
def test_node_help_message(mock_subprocess):
    base = """
Start StarkNet local network.

$ nile node
  Start StarkNet local network at port 5050

Options:
    """

    help_message = get_help_message()

    assert help_message == base + "\n options"


@patch("nile.core.node.subprocess.check_call")
def test_node_error(mock_subprocess, caplog):
    logging.getLogger().setLevel(logging.INFO)

    mock_subprocess.side_effect = FileNotFoundError

    node()
    assert (
        "\n\n😰 Could not find starknet-devnet, is it installed? Try with:\n"
        "    pip install starknet-devnet"
    ) in caplog.text
