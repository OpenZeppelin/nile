"""Command to start StarkNet local network."""

import logging
import subprocess

from nile.common import DEFAULT_GATEWAYS, write_node_json


def node(host="127.0.0.1", port=5050, node_args=None):
    """Start StarkNet local network."""
    try:
        # Save host and port information to be used by other commands
        if host == "127.0.0.1":
            network = "localhost"
        else:
            network = host
        gateway_url = f"http://{host}:{port}/"
        if DEFAULT_GATEWAYS.get(network) != gateway_url:
            write_node_json(network, gateway_url)

        command = ["starknet-devnet", "--host", host, "--port", str(port)]
        if node_args is not None:
            command += list(node_args)

        # Start network
        subprocess.check_call(command)

    except FileNotFoundError:
        logging.error(
            "\n\n😰 Could not find starknet-devnet, is it installed? Try with:\n"
            "    pip install starknet-devnet"
        )


def get_help_message():
    """Retrieve and parse the help message from starknet-devnet."""
    base = """
Start StarkNet local network.

$ nile node
  Start StarkNet local network at port 5050

Options:
    """

    raw_message = subprocess.check_output(["starknet-devnet", "--help"]).decode("utf-8")
    options_index = raw_message.find("optional arguments:")
    options = raw_message[options_index + 19 :]

    return base + options
