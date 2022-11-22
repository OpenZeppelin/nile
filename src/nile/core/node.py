"""Command to start StarkNet local network."""
import json
import logging
import subprocess

from nile.common import NODE_FILENAME, OTHER_NETWORKS


def node(host="127.0.0.1", port=5050, seed=None, lite_mode=False):
    """Start StarkNet local network."""
    try:
        # Save host and port information to be used by other commands
        file = NODE_FILENAME
        if host == "127.0.0.1":
            network = "localhost"
        else:
            network = host
        gateway_url = f"http://{host}:{port}/"
        gateways = {network: gateway_url, **OTHER_NETWORKS}

        with open(file, "w+") as f:
            json.dump(gateways, f, indent=2)

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
