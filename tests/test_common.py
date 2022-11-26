"""Tests for common library."""
import json
from unittest.mock import mock_open, patch

import pytest

from nile.common import (
    DEFAULT_GATEWAYS,
    NODE_FILENAME,
    create_node_json,
    get_gateways,
    parse_information,
    prepare_params,
    stringify,
)

NETWORK = "goerli"
ARGS = ["1", "2", "3"]
LIST1 = [1, 2, 3]
LIST2 = [1, 2, 3, [4, 5, 6]]
LIST3 = [1, 2, 3, [4, 5, 6, [7, 8, 9]]]
STDOUT_1 = "SDTOUT_1"
STDOUT_2 = "SDTOUT_2"
LOCAL_GATEWAY = {"localhost": "http://127.0.0.1:5050/"}


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


def test_get_gateways():
    gateways = get_gateways()
    expected = {**LOCAL_GATEWAY, **DEFAULT_GATEWAYS}
    assert gateways == expected

    # Check create_node_json is called with FileNotFoundError
    with patch("nile.common.create_node_json", return_value=LOCAL_GATEWAY) as mock_create:
        open_mock = mock_open()
        with patch("nile.common.open", open_mock):
            open_mock.side_effect = FileNotFoundError
            gateways = get_gateways()

            mock_create.assert_called_once()
            assert gateways == expected


@pytest.mark.parametrize(
    "args, gateway", [(None, LOCAL_GATEWAY), (["a", "b"], {"a": "b"})]
)
def test_create_node_json(args, gateway):
    open_mock = mock_open()
    with patch("nile.common.open", open_mock, create=True):
        if args is None:
            create_node_json()
        else:
            create_node_json(*args)

    expected = json.dumps({**gateway})

    open_mock.assert_called_with(NODE_FILENAME, "w")
    open_mock.return_value.write.assert_called_once_with(expected)
