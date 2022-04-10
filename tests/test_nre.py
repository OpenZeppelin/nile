"""
Tests for nre module.

Only unit tests for now.
"""

from unittest.mock import patch

from nile.nre import NileRuntimeEnvironment


def test_nre_loaded_plugins():
    def dummy():
        print("dummy_result")

    def dummy_params(a, b):
        return a + b

    with patch(
        "nile.nre.get_installed_plugins",
        return_value={"dummy": dummy, "dummy_params": dummy_params},
    ):
        nre = NileRuntimeEnvironment()
        assert callable(nre.dummy)
        dummy_result = dummy_params(1, 2)
        nre_result = nre.dummy_params(1, 2)
        assert dummy_result == nre_result
