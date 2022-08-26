"""Tests for node command."""
import logging
from unittest.mock import patch

import pytest

from nile.core.node import node

HOST = "127.0.0.1"
PORT = "5050"
SEED = "123"
LITE = "--lite-mode"


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.mark.parametrize(
    "args",
    [
        ({}),
        ({"seed": SEED}),
        ({"lite_mode": LITE}),
        ({"host": HOST, "port": PORT}),
        ({"host": HOST, "port": PORT, "seed": SEED, "lite_mode": LITE}),
    ],
)
@patch("nile.core.node.subprocess.check_call")
def test_node_call(mock_subprocess, args):
    node(**args)

    command = ["starknet-devnet", "--host", HOST, "--port", PORT]
    if "seed" in args:
        command.append("--seed")
        command.append(SEED)
    if "lite_mode" in args:
        command.append(LITE)
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
