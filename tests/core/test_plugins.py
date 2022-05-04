"""
Tests for plugins in core module.

Only unit tests for now.
"""

from unittest.mock import patch

import click

from nile.core.plugins import get_installed_plugins, load_plugins, skip_click_exit


def test_skip_click_exit():
    @click.command()
    @click.argument("a", type=int)
    @click.argument("b", type=int)
    def dummy_method(a, b):
        return a + b

    decorated = skip_click_exit(dummy_method)
    decorated_result = decorated(["1", "2"])

    assert callable(decorated)
    assert decorated_result == 3


def testget_installed_plugins():
    class Dummy:
        value = "nile.core.plugins.get_installed_plugins"
        name = "get_installed_plugins"

    with patch("nile.core.plugins.entry_points", return_value=[Dummy()]):
        installed_plugins = get_installed_plugins()
        assert "get_installed_plugins" in installed_plugins


def test_load_plugins():
    @click.group()
    def cli():
        """Nile CLI group."""
        pass

    @click.command()
    def dummy():
        print("dummy_result")

    with patch(
        "nile.core.plugins.get_installed_plugins", return_value={"dummy": dummy}
    ):
        app = load_plugins(cli)
        assert callable(app)
