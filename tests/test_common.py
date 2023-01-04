"""Tests for common library."""

import json

import pytest

from nile.common import (
    DEFAULT_GATEWAYS,
    NODE_FILENAME,
    get_gateways,
    parse_information,
    prepare_params,
    stringify,
    write_node_json,
)

NETWORK = "goerli"
ARGS = ["1", "2", "3"]
LIST1 = [1, 2, 3]
LIST2 = [1, 2, 3, [4, 5, 6]]
LIST3 = [1, 2, 3, [4, 5, 6, [7, 8, 9]]]
STDOUT_1 = "SDTOUT_1"
STDOUT_2 = "SDTOUT_2"


@pytest.fixture(autouse=True)
def tmp_working_dir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.mark.parametrize(
    "args, expected",
    [
        ([], []),
        ([LIST1], [["1", "2", "3"]]),
        ([LIST2], [["1", "2", "3", ["4", "5", "6"]]]),
        ([LIST3], [["1", "2", "3", ["4", "5", "6", ["7", "8", "9"]]]]),
    ],
)
def test_stringify(args, expected):
    assert stringify(args) == expected


@pytest.mark.parametrize(
    "args, expected",
    [
        ([], []),
        ([LIST1], [["1", "2", "3"]]),
        (
            ["MyToken name", "MyToken symbol"],
            ["23977024514528806274181721445", "1571358278584159847990373933805420"],
        ),
        (["0xbad", 1234, "1234", "bad"], ["0xbad", "1234", "1234", "6447460"]),
    ],
)
def test_prepare_params(args, expected):
    assert prepare_params(args) == expected


def test_parse_information():
    a = format(1, "#066x")
    b = format(2, "#066x")
    target = f"Formatting 'a': {a}. Formatting 'b': {b}."

    _a, _b = parse_information(target)
    assert _a, _b == (a, b)


@pytest.mark.parametrize(
    "network, url, gateway",
    [
        (None, None, {}),
        ("localhost", "5051", {"localhost": "5051"}),
        ("host", "port", {"host": "port"}),
    ],
)
def test_get_gateways(network, url, gateway):
    if network is not None:
        write_node_json(network, url)

    gateways = get_gateways()
    expected = {**DEFAULT_GATEWAYS, **gateway}
    assert gateways == expected

    # Check that node.json gateway returns in the case of duplicate keys
    if network == "localhost":
        assert expected["localhost"] != "5050"
        assert expected["localhost"] == "5051"


@pytest.mark.parametrize(
    "args1, args2, gateways",
    [
        (
            ["NETWORK1", "URL1"],
            ["NETWORK2", "URL2"],
            {"NETWORK1": "URL1", "NETWORK2": "URL2"},
        ),
    ],
)
def test_write_node_json(args1, args2, gateways):
    # Check that node.json is created and adds keys
    write_node_json(*args1)
    write_node_json(*args2)

    with open(NODE_FILENAME, "r") as fp:
        result = fp.read()
        expected = json.dumps(gateways, indent=2)
        assert result == expected
