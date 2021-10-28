"""Compile command tests."""
import os
import sys
sys.path.append(os.path.abspath(os.path.join("..", "src")))

# pylint: disable=E402
from click.testing import CliRunner
# pylint: disable=E402
from src.nile.main import cli


def test_compile():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["compile", "--disable_hint_validation"], catch_exceptions=True
    )
    assert result.exit_code == 0
