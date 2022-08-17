"""Tests for common library."""
from unittest.mock import patch

import pytest

from nile.common import BUILD_DIRECTORY, prepare_params, run_command, stringify

CONTRACT = "contract"
OPERATION = "invoke"
NETWORK = "goerli"
ARGS = ["1", "2", "3"]
LIST1 = [1, 2, 3]
LIST2 = [1, 2, 3, [4, 5, 6]]
LIST3 = [1, 2, 3, [4, 5, 6, [7, 8, 9]]]


@pytest.mark.parametrize("operation", ["invoke", "call"])
@patch("nile.common.subprocess.check_output")
def test_run_command(mock_subprocess, operation):

    run_command(
        contract_name=CONTRACT, network=NETWORK, operation=operation, arguments=ARGS
    )

    mock_subprocess.assert_called_once_with(
        [
            "starknet",
            operation,
            "--contract",
            f"{BUILD_DIRECTORY}/{CONTRACT}.json",
            "--inputs",
            *ARGS,
            "--no_wallet",
        ]
    )


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
    ],
)
def test_prepare_params(args, expected):
    assert prepare_params(args) == expected
