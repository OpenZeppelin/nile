"""Tests for accounts file."""

import json

import pytest

from nile.accounts import register, unregister
from nile.common import ACCOUNTS_FILENAME
from nile.utils import hex_address

NETWORK = "localhost"
NETWORK_FILE = NETWORK + ACCOUNTS_FILENAME

PUBKEYS = [1, 2, 3]
ADDRESSES = [4, 5, 6]
INDEXES = [0, 1, 2]
ALIASES = ["A1", "A2", "A3"]

ARGS_0 = (PUBKEYS[0], ADDRESSES[0], INDEXES[0], ALIASES[0], NETWORK)
ARGS_1 = (PUBKEYS[1], ADDRESSES[1], INDEXES[1], ALIASES[1], NETWORK)
ARGS_2 = (PUBKEYS[2], ADDRESSES[2], INDEXES[2], ALIASES[2], NETWORK)

ACCOUNT_0 = {
    hex(PUBKEYS[0]): {"address": hex_address(ADDRESSES[0]), "index": 0, "alias": "A1"}
}
ACCOUNT_1 = {
    hex(PUBKEYS[1]): {"address": hex_address(ADDRESSES[1]), "index": 1, "alias": "A2"}
}
ACCOUNT_2 = {
    hex(PUBKEYS[2]): {"address": hex_address(ADDRESSES[2]), "index": 2, "alias": "A3"}
}
ALL_ACCOUNTS = {**ACCOUNT_0, **ACCOUNT_1, **ACCOUNT_2}


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_unregister():
    register(*ARGS_0)
    register(*ARGS_1)
    register(*ARGS_2)

    # Check dict
    with open(f"{NETWORK}.{ACCOUNTS_FILENAME}", "r") as fp:
        lines = fp.read()
        expected = json.dumps(ALL_ACCOUNTS, indent=2)
        assert lines == expected

    unregister(hex_address(ADDRESSES[1]), NETWORK)

    # Check dict
    with open(f"{NETWORK}.{ACCOUNTS_FILENAME}", "r") as fp:
        lines = fp.read()
        new_accounts = {**ACCOUNT_0, **ACCOUNT_2}
        expected = json.dumps(new_accounts, indent=2)
        assert lines == expected
        assert hex(PUBKEYS[1]) not in lines


def test_unregister_with_wrong_address():
    register(*ARGS_0)
    register(*ARGS_1)
    register(*ARGS_2)

    unregister(hex_address("0xbad"), NETWORK)

    # Check dict
    with open(f"{NETWORK}.{ACCOUNTS_FILENAME}", "r") as fp:
        lines = fp.read()
        expected = json.dumps(ALL_ACCOUNTS, indent=2)
        assert lines == expected
