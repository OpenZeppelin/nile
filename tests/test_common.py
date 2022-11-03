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


@pytest.mark.parametrize("operation", ["invoke", "call", "deploy", "declare"])
@pytest.mark.parametrize("signature", [None])
@pytest.mark.parametrize("max_fee", [0, 5, None])
@pytest.mark.parametrize("query_flag", ["simulate", "estimate_fee", None])
@pytest.mark.parametrize("mainnet_token", ["token_test", None])
@patch("nile.common.subprocess.check_output")
def test_run_command(
    mock_subprocess, operation, signature, max_fee, query_flag, mainnet_token
):

    run_command(
        contract_name=CONTRACT,
        network=NETWORK,
        operation=operation,
        inputs=ARGS,
        signature=signature,
        max_fee=max_fee,
        query_flag=query_flag,
        mainnet_token=mainnet_token,
    )

    exp_command = [
        "starknet",
        operation,
        "--contract",
        f"{BUILD_DIRECTORY}/{CONTRACT}.json",
        "--inputs",
        *ARGS,
    ]

    # Add signature
    if signature is not None:
        exp_command.extend(["--signature", signature])

    # Add max_fee
    if max_fee is not None:
        exp_command.extend(["--max_fee", max_fee])

    # Add mainnet_token
    if mainnet_token is not None:
        exp_command.extend(["--token", mainnet_token])

    # Add query_flag
    if query_flag is not None:
        exp_command.extend([f"--{query_flag}"])

    exp_command.append("--no_wallet")

    mock_subprocess.assert_called_once_with(exp_command)


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
