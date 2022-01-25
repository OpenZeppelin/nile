"""Tests for cli.py."""
import json
import shutil
import sys
from multiprocessing import Process
from os import getpid, kill
from pathlib import Path
from signal import SIGINT
from threading import Timer
from time import sleep
from urllib.error import URLError
from urllib.request import urlopen

import pytest
from click.testing import CliRunner

from nile.cli import cli
from nile.common import (
    ABIS_DIRECTORY,
    BUILD_DIRECTORY,
    CONTRACTS_DIRECTORY,
    NODE_FILENAME,
)

RESOURCES_DIR = Path(__file__).parent / "resources"


pytestmark = pytest.mark.end_to_end


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def create_process(target, args):
    """Spawns another process in Python."""
    p = Process(target=target, args=args)
    return p


def start_node(seconds, node_args):
    """Start node with host and port specified in node_args and life in seconds."""
    # Timed kill command with SIGINT to close Node process
    Timer(seconds, lambda: kill(getpid(), SIGINT)).start()
    CliRunner().invoke(cli, ["node", *node_args])


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


def test_clean():
    # The implementation is already thoroughly covered by unit tests, so here
    # we just check whether the command completes successfully.
    result = CliRunner().invoke(cli, ["clean"])
    assert result.exit_code == 0


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
def test_compile(args, expected):
    contract_source = RESOURCES_DIR / "contracts" / "contract.cairo"

    target_dir = Path(CONTRACTS_DIRECTORY)
    target_dir.mkdir()

    shutil.copyfile(contract_source, target_dir / "contract_1.cairo")
    shutil.copyfile(contract_source, target_dir / "contract_2.cairo")

    abi_dir = Path(ABIS_DIRECTORY)
    build_dir = Path(BUILD_DIRECTORY)

    assert not abi_dir.exists()
    assert not build_dir.exists()

    result = CliRunner().invoke(cli, ["compile", *args])
    assert result.exit_code == 0

    assert {f.name for f in abi_dir.glob("*.json")} == expected
    assert {f.name for f in build_dir.glob("*.json")} == expected


@pytest.mark.parametrize(
    "args, expected",
    [
        ([], "http://localhost:5000/"),
        (["--host", "localhost", "--port", "5001"], "http://localhost:5001/"),
    ],
)
@pytest.mark.xfail(
    sys.version_info >= (3, 10),
    reason="Issue in cairo-lang. "
    "See https://github.com/starkware-libs/cairo-lang/issues/27",
)
def test_node(args, expected):
    # Node life
    seconds = 8

    if args == []:
        host, port = "localhost", 5000
    else:
        host, port = args[1], int(args[3])

    network = host
    gateway_url = f"http://{host}:{port}/"

    # Spawn process to start StarkNet local network with specified port
    # i.e. $ nile node --host localhost --port 5001
    p = create_process(target=start_node, args=(seconds, args))
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
