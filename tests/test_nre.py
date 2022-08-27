"""
Tests for nre module.

Only unit tests for now.
"""
from unittest.mock import patch

import click

from nile.nre import NileRuntimeEnvironment


def test_nre_loaded_plugins():
    @click.command()
    def dummy():
        print("dummy_result")

    @click.command()
    @click.argument("a", type=int)
    @click.argument("b", type=int)
    def dummy_params(a, b):
        return a + b

    with patch(
        "nile.nre.get_installed_plugins",
        return_value={"dummy": dummy, "dummy_params": dummy_params},
    ):
        nre = NileRuntimeEnvironment()
        assert callable(nre.dummy)

        nre_result = nre.dummy_params(["1", "2"])
        assert 3 == nre_result


def test_nre_get_accounts(capsys):
    nre = NileRuntimeEnvironment()
    with patch("nile.nre.get_accounts", return_value=(123)):
        res = nre.get_accounts()
        captured = capsys.readouterr()

        assert res == (123)
        assert str(captured.out) == ""
        assert str(captured.err) == ""


def test_nre_get_accounts_without_registered_accounts(capsys):
    nre = NileRuntimeEnvironment()

    res = nre.get_accounts()
    captured = capsys.readouterr()

    assert res is None
    assert str(captured.err) == ""
    assert "❌ No registered accounts detected in localhost.accounts.json" in str(
        captured.out
    )
    assert (
        "For more info, see https://github.com/OpenZeppelin/nile#get-accounts"
        in str(captured.out)
    )
