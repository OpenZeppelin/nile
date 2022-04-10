"""Nile plugins utility methods."""
import functools
import importlib
from typing import Dict

from click import Group
from importlib_metadata import entry_points


def skip_click_exit(func):
    """
    When a click command is executed programatically a SystemExit is executed.

    This decorator avoids SystemExit when execution is finished.
    """

    @functools.wraps(func)
    # Click commands only manages keyword arguments
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SystemExit:
            pass

    return wrapper


def get_installed_plugins() -> Dict:
    """
    Get the name and object of installed Nile plugins.

    Returns:
        Dict: dictionary with plugin name as key and value with the plugin object
    """
    discovered_plugins = entry_points(group="nile_plugins")
    loaded_plugins = {}
    for plugin in discovered_plugins:
        package_name = plugin.value.rsplit(".", 1)[0]
        package_object = importlib.import_module(package_name)
        plugin_call = getattr(package_object, plugin.name)
        loaded_plugins[plugin.name] = plugin_call
    return loaded_plugins


def load_plugins(app) -> Group:
    """
    Add plugin entrypoints to Click app.

    Args:
        app (click.group): main cli app

    Returns:
        Group: click app with plugins commands added
    """
    for name, plugin_object in get_installed_plugins().items():
        app.add_command(plugin_object, name)
    return app
