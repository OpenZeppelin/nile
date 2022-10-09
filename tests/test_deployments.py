"""Tests for deployments file."""
import pytest

from nile.common import DEPLOYMENTS_FILENAME
from nile.deployments import register, update_abi
from nile.utils import normalize_number

LOCALHOST = "localhost"

A_ADDR = "0x0000000000000000000000000000000000000000000000000000000000000001"
A_ABI = "artifacts/abis/a.json"
A_ABI_2 = "artifacts/abis/a2.json"
A_ALIAS = "contractA"
A_ALIAS_ALT = "altA"

B_ADDR = "0x0000000000000000000000000000000000000000000000000000000000000002"
B_ABI = "artifacts/abis/b.json"
B_ABI_2 = "artifacts/abis/b2.json"
B_ALIAS = "contractB"

C_ADDR = "0x0000000000000000000000000000000000000000000000000000000000000003"
C_ABI = "artifacts/abis/c.json"
C_ABI_2 = "artifacts/abis/c2.json"


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.mark.parametrize(
    "address_or_alias, abi, expected_lines",
    [
        (
            normalize_number(A_ADDR),
            A_ABI_2,
            [
                f"{A_ADDR}:{A_ABI_2}:{A_ALIAS}:{A_ALIAS_ALT}",
                f"{B_ADDR}:{B_ABI}:{B_ALIAS}",
                f"{C_ADDR}:{C_ABI}",
            ],
        ),
        (
            A_ALIAS,
            A_ABI_2,
            [
                f"{A_ADDR}:{A_ABI_2}:{A_ALIAS}:{A_ALIAS_ALT}",
                f"{B_ADDR}:{B_ABI}:{B_ALIAS}",
                f"{C_ADDR}:{C_ABI}",
            ],
        ),
        (
            A_ALIAS_ALT,
            A_ABI_2,
            [
                f"{A_ADDR}:{A_ABI_2}:{A_ALIAS}:{A_ALIAS_ALT}",
                f"{B_ADDR}:{B_ABI}:{B_ALIAS}",
                f"{C_ADDR}:{C_ABI}",
            ],
        ),
        (
            B_ALIAS,
            B_ABI_2,
            [
                f"{A_ADDR}:{A_ABI}:{A_ALIAS}:{A_ALIAS_ALT}",
                f"{B_ADDR}:{B_ABI_2}:{B_ALIAS}",
                f"{C_ADDR}:{C_ABI}",
            ],
        ),
        (
            normalize_number(C_ADDR),
            C_ABI_2,
            [
                f"{A_ADDR}:{A_ABI}:{A_ALIAS}:{A_ALIAS_ALT}",
                f"{B_ADDR}:{B_ABI}:{B_ALIAS}",
                f"{C_ADDR}:{C_ABI_2}",
            ],
        ),
    ],
)
def test_update_deployment(address_or_alias, abi, expected_lines):
    register(normalize_number(A_ADDR), A_ABI, LOCALHOST, f"{A_ALIAS}:{A_ALIAS_ALT}")
    register(normalize_number(B_ADDR), B_ABI, LOCALHOST, B_ALIAS)
    register(normalize_number(C_ADDR), C_ABI, LOCALHOST, None)

    with open(f"{LOCALHOST}.{DEPLOYMENTS_FILENAME}", "r") as fp:
        lines = fp.readlines()
    assert len(lines) == 3

    update_abi(address_or_alias, abi, LOCALHOST)

    with open(f"{LOCALHOST}.{DEPLOYMENTS_FILENAME}", "r") as fp:
        lines = fp.readlines()
    assert len(lines) == 3

    assert lines[0].strip() == expected_lines[0]
    assert lines[1].strip() == expected_lines[1]
    assert lines[2].strip() == expected_lines[2]


def test_update_non_existent_identifier():
    try:
        update_abi("invalid", A_ABI, LOCALHOST)
        raise AssertionError("update expected to fail due to missing deployment")
    except Exception as e:
        assert "does not exist" in str(e)
