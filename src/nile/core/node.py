"""Command to start StarkNet local network."""

import logging
import subprocess

from nile.common import DEFAULT_GATEWAYS, write_node_json


def node(host="127.0.0.1", port=5050, seed=None, lite_mode=False):
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

        if seed is not None:
            command.append("--seed")
            command.append(str(seed))

        if lite_mode:
            command.append("--lite-mode")

        # Start network
        subprocess.check_call(command)

    except FileNotFoundError:
        logging.error(
            "\n\n😰 Could not find starknet-devnet, is it installed? Try with:\n"
            "    pip install starknet-devnet"
        )
