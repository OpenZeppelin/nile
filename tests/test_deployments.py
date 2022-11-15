"""Tests for deployments file."""
import logging

import pytest

from nile.common import DECLARATIONS_FILENAME, DEPLOYMENTS_FILENAME
from nile.deployments import register, register_class_hash, unregister, update_abi
from nile.utils import hex_address, hex_class_hash, normalize_number

LOCALHOST = "localhost"

CLASS_HASH = 111

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
def test_update_deployment(address_or_alias, abi, expected_lines, caplog):
    register(normalize_number(A_ADDR), A_ABI, LOCALHOST, f"{A_ALIAS}:{A_ALIAS_ALT}")
    register(normalize_number(B_ADDR), B_ABI, LOCALHOST, B_ALIAS)
    register(normalize_number(C_ADDR), C_ABI, LOCALHOST, None)

    with open(f"{LOCALHOST}.{DEPLOYMENTS_FILENAME}", "r") as fp:
        lines = fp.readlines()
    assert len(lines) == 3

    # make logs visible to test
    logging.getLogger().setLevel(logging.INFO)

    update_abi(address_or_alias, abi, LOCALHOST)

    identifier = address_or_alias
    if type(address_or_alias) is int:
        identifier = hex_address(address_or_alias)
    assert f"Updating {identifier} in {LOCALHOST}.{DEPLOYMENTS_FILENAME}" in caplog.text

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


def test_unregister():
    args_a = {
        "address": normalize_number(A_ADDR),
        "abi": A_ABI,
        "network": LOCALHOST,
        "alias": f"{A_ALIAS}:{A_ALIAS_ALT}",
    }
    args_b = {
        "address": normalize_number(B_ADDR),
        "abi": B_ABI,
        "network": LOCALHOST,
        "alias": f"{B_ALIAS}",
    }
    args_c = {
        "address": normalize_number(C_ADDR),
        "abi": C_ABI,
        "network": LOCALHOST,
        "alias": None,
    }
    register(**args_a)
    register(**args_b)
    register(**args_c)

    with open(f"{LOCALHOST}.{DEPLOYMENTS_FILENAME}", "r") as fp:
        lines = fp.readlines()
    assert len(lines) == 3

    # unregister uses a different kwarg so this copies and updates the dict
    # and deletes the unused address kwarg
    unregister_args = args_b
    unregister_args["address_or_class_hash"] = unregister_args["address"]
    del unregister_args["address"]

    unregister(**unregister_args)

    with open(f"{LOCALHOST}.{DEPLOYMENTS_FILENAME}", "r") as fp:
        lines = fp.readlines()
    assert len(lines) == 2

    assert lines[0].strip() == f"{A_ADDR}:{A_ABI}:{A_ALIAS}:{A_ALIAS_ALT}"
    assert lines[1].strip() == f"{C_ADDR}:{C_ABI}"


def test_register_class_hash():
    args = {
        "hash": CLASS_HASH,
        "network": LOCALHOST,
        "alias": f"{A_ALIAS}:{A_ALIAS_ALT}",
    }
    register_class_hash(**args)

    with open(f"{LOCALHOST}.{DECLARATIONS_FILENAME}", "r") as fp:
        lines = fp.readlines()
    assert len(lines) == 1

    assert lines[0].strip() == f"{hex_class_hash(CLASS_HASH)}:{A_ALIAS}:{A_ALIAS_ALT}"

    # try registering the same hash
    try:
        register_class_hash(**args)
        raise AssertionError("register expected to fail due to existing declaration")
    except Exception as e:
        assert "Hash 0x0000...00006f already exists" in str(e)

    with open(f"{LOCALHOST}.{DECLARATIONS_FILENAME}", "r") as fp:
        lines = fp.readlines()
    assert len(lines) == 1

    assert lines[0].strip() == f"{hex_class_hash(CLASS_HASH)}:{A_ALIAS}:{A_ALIAS_ALT}"
