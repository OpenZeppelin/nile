"""Tests for deployments file."""
import pytest

from nile.common import DEPLOYMENTS_FILENAME
from nile.deployments import load, register, update

LOCALHOST = "localhost"

CONTRACT_A = ("0x01", "artifacts/abis/a.json", None)
CONTRACT_B = ("0x02", "artifacts/abis/b.json", "contractB")
CONTRACT_C = ("0x03", "artifacts/abis/c.json", None)

CONTRACT_A2 = ("0x01", "artifacts/abis/a2.json", None)
CONTRACT_B2 = ("0x02", "artifacts/abis/b2.json", "contractB2")
CONTRACT_C2 = ("0x03", "artifacts/abis/c2.json", "contractC2")


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.mark.parametrize(
    "update_item, expected_items",
    [
        (CONTRACT_A2, [CONTRACT_A2, CONTRACT_B, CONTRACT_C]),
        (CONTRACT_B2, [CONTRACT_A, CONTRACT_B2, CONTRACT_C]),
        (CONTRACT_C2, [CONTRACT_A, CONTRACT_B, CONTRACT_C2]),
    ],
)
def test_update_deployment(update_item, expected_items):
    register(CONTRACT_A[0], CONTRACT_A[1], LOCALHOST, CONTRACT_A[2])
    register(CONTRACT_B[0], CONTRACT_B[1], LOCALHOST, CONTRACT_B[2])
    register(CONTRACT_C[0], CONTRACT_C[1], LOCALHOST, CONTRACT_C[2])

    update(update_item[0], update_item[1], LOCALHOST, update_item[2])

    with open(f"{LOCALHOST}.{DEPLOYMENTS_FILENAME}", "r") as fp:
        lines = fp.readlines()
    assert len(lines) == 3

    assert_load(expected_items[0])
    assert_load(expected_items[1])
    assert_load(expected_items[2])


def assert_load(expected_item):
    address, abi = next(load(expected_item[0], LOCALHOST), None)
    assert address == expected_item[0]
    assert abi == expected_item[1]

    alias = expected_item[2]
    if alias is not None:
        address, abi = next(load(alias, LOCALHOST), None)
        assert address == expected_item[0]
        assert abi == expected_item[1]
