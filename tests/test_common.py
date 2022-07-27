"""Tests for deploy command."""
from unittest.mock import patch

import pytest

from nile.common import BUILD_DIRECTORY, run_command

CONTRACT = "contract"
OPERATION = "invoke"
NETWORK = "goerli"
ARGS = [1, 2, 3]


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
