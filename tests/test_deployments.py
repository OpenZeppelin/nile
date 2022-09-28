"""Tests for deployments file."""
import pytest

from nile.common import DEPLOYMENTS_FILENAME
from nile.deployments import load, register, update

LOCALHOST = "localhost"

CONTRACT_A = ("0x01", "artifacts/abis/a.json", "contractA")
CONTRACT_B = ("0x02", "artifacts/abis/b.json", "contractB")
CONTRACT_C = ("0x03", "artifacts/abis/c.json", None)

CONTRACT_A_UPDATE = ("0x01", "artifacts/abis/a2.json")
CONTRACT_A_EXPECTED = ("0x01", "artifacts/abis/a2.json", "contractA")

CONTRACT_B_UPDATE = ("contractB", "artifacts/abis/b2.json")
CONTRACT_B_EXPECTED = ("0x02", "artifacts/abis/b2.json", "contractB")

CONTRACT_C_UPDATE = ("0x03", "artifacts/abis/c2.json")
CONTRACT_C_EXPECTED = ("0x03", "artifacts/abis/c2.json", None)


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.mark.parametrize(
    "update_item, expected_items",
    [
        (CONTRACT_A_UPDATE, [CONTRACT_A_EXPECTED, CONTRACT_B, CONTRACT_C]),
        (CONTRACT_B_UPDATE, [CONTRACT_A, CONTRACT_B_EXPECTED, CONTRACT_C]),
        (CONTRACT_C_UPDATE, [CONTRACT_A, CONTRACT_B, CONTRACT_C_EXPECTED]),
    ],
)
def test_update_deployment(update_item, expected_items):
    register(CONTRACT_A[0], CONTRACT_A[1], LOCALHOST, CONTRACT_A[2])
    register(CONTRACT_B[0], CONTRACT_B[1], LOCALHOST, CONTRACT_B[2])
    register(CONTRACT_C[0], CONTRACT_C[1], LOCALHOST, CONTRACT_C[2])

    with open(f"{LOCALHOST}.{DEPLOYMENTS_FILENAME}", "r") as fp:
        lines = fp.readlines()
    assert len(lines) == 3

    update(update_item[0], update_item[1], LOCALHOST)

    with open(f"{LOCALHOST}.{DEPLOYMENTS_FILENAME}", "r") as fp:
        lines = fp.readlines()
    assert len(lines) == 3

    assert_load(expected_items[0])
    assert_load(expected_items[1])
    assert_load(expected_items[2])

    try:
        update("invalid", CONTRACT_A[1], LOCALHOST)
        raise AssertionError("update expected to fail due to missing deployment")
    except Exception as e:
        assert "does not exist" in str(e)


def assert_load(expected_item):
    address, abi = next(load(expected_item[0], LOCALHOST), None)
    assert address == expected_item[0]
    assert abi == expected_item[1]

    alias = expected_item[2]
    if alias is not None:
        address, abi = next(load(alias, LOCALHOST), None)
        assert address == expected_item[0]
        assert abi == expected_item[1]
