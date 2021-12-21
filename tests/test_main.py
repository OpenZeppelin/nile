"""Tests for main.py."""
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from nile.common import (
    ABIS_DIRECTORY,
    BUILD_DIRECTORY,
    CONTRACTS_DIRECTORY,
)
from nile.main import cli

RESOURCES_DIR = Path(__file__).parent / "resources"


pytestmark = pytest.mark.end_to_end


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


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
