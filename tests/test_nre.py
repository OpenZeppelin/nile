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
