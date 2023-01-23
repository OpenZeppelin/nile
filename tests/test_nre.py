"""
Tests for nre module.

Only unit tests for now.
"""

from unittest.mock import patch

import pytest

from nile.nre import NileRuntimeEnvironment


def dummy():
    print("dummy_result")


def dummy_params(nre, a, b):
    return a + b


def bad_params(a, b):
    return a + b


@pytest.mark.parametrize(
    "plugin_name_and_object, will_fail",
    [
        ({"dummy": dummy, "dummy_params": dummy_params}, False),
        ({"dummy": dummy, "dummy_params": bad_params}, True),
    ],
)
@patch("nile.nre.get_installed_plugins")
def test_nre_loaded_plugins(mock_plugins, plugin_name_and_object, will_fail):
    mock_plugins.return_value = plugin_name_and_object
    nre = NileRuntimeEnvironment()

    assert callable(nre.dummy)

    if will_fail:
        with pytest.raises(TypeError):
            nre.dummy_params(1, 2)
    else:
        nre_result = nre.dummy_params(1, 2)
        assert 3 == nre_result
