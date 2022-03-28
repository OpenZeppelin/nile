"""
Tests for utils in core module.

Only unit tests for now.
"""

from unittest.mock import patch

import click

from nile.core.utils import _get_installed_plugins, load_plugins, skip_click_exit


def test_skip_click_exit():
    def dummy_method(a, b):
        return a + b

    dummy_result = dummy_method(1, 2)
    decorated = skip_click_exit(dummy_method)
    decorated_result = decorated(1, 2)

    assert callable(decorated)
    assert dummy_result == decorated_result


def test_get_installed_plugins():
    class Dummy:
        value = "nile.core.utils._get_installed_plugins"
        name = "_get_installed_plugins"

    with patch("nile.core.utils.entry_points", return_value=[Dummy()]):
        installed_plugins = _get_installed_plugins()
        assert "_get_installed_plugins" in installed_plugins


def test_load_plugins():
    @click.group()
    def cli():
        """Nile CLI group."""
        pass

    def dummy():
        print("dummy_result")

    with patch("nile.core.utils._get_installed_plugins", return_value={"dummy": dummy}):
        app = load_plugins(cli)
        assert callable(app)
