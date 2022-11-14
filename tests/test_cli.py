"""Tests for cli.py."""
import itertools
import json
import shutil
import sys
from multiprocessing import Process
from os import getpid, kill
from pathlib import Path
from signal import SIGINT
from threading import Timer
from time import sleep
from unittest.mock import AsyncMock, patch
from urllib.error import URLError
from urllib.request import urlopen

import pytest
from asyncclick.testing import CliRunner

from nile.cli import cli
from nile.common import (
    ABIS_DIRECTORY,
    BUILD_DIRECTORY,
    CONTRACTS_DIRECTORY,
    NODE_FILENAME,
)
from nile.utils import hex_class_hash

RESOURCES_DIR = Path(__file__).parent / "resources"
MOCK_HASH = "0x123"


pytestmark = pytest.mark.end_to_end


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def create_process(target, args):
    """Spawns another process in Python."""
    p = Process(target=target, args=args)
    return p


async def start_node(seconds, node_args):
    """Start node with host and port specified in node_args and life in seconds."""
    # Timed kill command with SIGINT to close Node process
    Timer(seconds, lambda: kill(getpid(), SIGINT)).start()
    await CliRunner().invoke(cli, ["node", *node_args])


def check_node(p, seconds, gateway_url):
    """Check if node is running while spawned process is alive."""
    check_runs = 0
    while p.is_alive and check_runs < seconds:
        try:
            status = urlopen(gateway_url + "is_alive").getcode()
            return status
        except URLError:
            check_runs += 1
            sleep(1)
            continue


@pytest.mark.asyncio
async def test_clean():
    # The implementation is already thoroughly covered by unit tests, so here
    # we just check whether the command completes successfully.
    result = await CliRunner().invoke(cli, ["clean"])
    assert result.exit_code == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, expected",
    [
        ([], {"contract_1.json", "contract_2.json"}),
        (["contract_1.cairo"], {"contract_1.json"}),
        (["contract_2.cairo"], {"contract_2.json"}),
    ],
)
@pytest.mark.xfail(
    sys.version_info >= (3, 10),
    reason="Issue in cairo-lang. "
    "See https://github.com/starkware-libs/cairo-lang/issues/27",
)
async def test_compile(args, expected):
    contract_source = RESOURCES_DIR / "contracts" / "contract.cairo"

    target_dir = Path(CONTRACTS_DIRECTORY)
    target_dir.mkdir()

    shutil.copyfile(contract_source, target_dir / "contract_1.cairo")
    shutil.copyfile(contract_source, target_dir / "contract_2.cairo")

    abi_dir = Path(ABIS_DIRECTORY)
    build_dir = Path(BUILD_DIRECTORY)

    assert not abi_dir.exists()
    assert not build_dir.exists()

    result = await CliRunner().invoke(cli, ["compile", *args])
    assert result.exit_code == 0

    assert {f.name for f in abi_dir.glob("*.json")} == expected
    assert {f.name for f in build_dir.glob("*.json")} == expected


@pytest.mark.asyncio
@pytest.mark.xfail(
    sys.version_info >= (3, 10),
    reason="Issue in cairo-lang. "
    "See https://github.com/starkware-libs/cairo-lang/issues/27",
)
@patch("nile.core.node.subprocess")
async def test_node_forwards_args(mock_subprocess):
    args = [
        "--host",
        "localhost",
        "--port",
        "5001",
        "--seed",
        "1234",
    ]

    result = await CliRunner().invoke(cli, ["node", *args])
    assert result.exit_code == 0

    expected = ["starknet-devnet", *args]
    mock_subprocess.check_call.assert_called_once_with(expected)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "opts, expected",
    [
        ({}, "http://127.0.0.1:5050/"),
        ({"--host": "localhost", "--port": "5001"}, "http://localhost:5001/"),
        ({"--seed": "1234"}, "http://127.0.0.1:5050/"),
    ],
)
@pytest.mark.xfail(
    sys.version_info >= (3, 10),
    reason="Issue in cairo-lang. "
    "See https://github.com/starkware-libs/cairo-lang/issues/27",
)
async def test_node_runs_gateway(opts, expected):
    # Node life
    seconds = 15

    host = opts.get("--host", "127.0.0.1")
    port = opts.get("--port", "5050")

    if host == "127.0.0.1":
        network = "localhost"
    else:
        network = host

    gateway_url = f"http://{host}:{port}/"

    # Convert opts to arg list -
    #   { "--host": "localhost", "--port":  "5001" } =>
    #   [ "--host", "localhost", "--port", "5001" ]
    args = itertools.chain.from_iterable(opts.items())

    # Spawn process to start StarkNet local network with specified port
    # i.e. $ nile node --host localhost --port 5001
    init_node = await start_node(seconds, args)
    p = create_process(target=init_node, args=(seconds, args))
    p.start()

    # Check node heartbeat and assert that it is running
    status = check_node(p, seconds, gateway_url)
    p.join()
    assert status == 200

    # Assert network and gateway_url is correct in node.json file
    file = NODE_FILENAME
    with open(file, "r") as f:
        gateway = json.load(f)
    assert gateway.get(network) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args",
    [
        ([MOCK_HASH, "--network", "goerli"]),
        ([MOCK_HASH, "--network", "goerli2"]),
        ([MOCK_HASH, "--network", "integration"]),
        ([MOCK_HASH, "--network", "mainnet", "--contracts_file", "example.txt"]),
    ],
)
async def test_status(args):
    with patch("nile.utils.status.execute_call", new=AsyncMock()) as mock_execute:
        mock_execute.return_value = json.dumps({"tx_status": "ACCEPTED_ON_L2"})

        result = await CliRunner().invoke(cli, ["status", *args])

        # Check status
        assert result.exit_code == 0

        # Check internals
        network = args[2]
        command_args = {"hash": hex_class_hash(MOCK_HASH)}

        mock_execute.assert_called_once_with("tx_status", network, **command_args)
