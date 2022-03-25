"""Nile core utils."""
import importlib

from click import Group
from importlib_metadata import entry_points


def load_plugins(app) -> Group:
    """
    Add plugin entrypoints to Click app.

    Args:
        app (click.group): main cli app

    Returns:
        Group: click app with plugins commands added
    """
    discovered_plugins = entry_points(group="nile_plugins")
    for plugin in discovered_plugins:
        package_name = plugin.value.rsplit(".", 1)[0]
        package_object = importlib.import_module(package_name)
        plugin_call = getattr(package_object, plugin.name)
        app.add_command(plugin_call, plugin.name)
    return app
