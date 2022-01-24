"""Command to start StarkNet local network."""
import json
import subprocess

from nile.common import NODE_FILENAME


def node(host="localhost", port=5000):
    """Start StarkNet local network."""
    try:
        # Save host and port information to be used by other commands
        file = NODE_FILENAME
        network = host
        gateway_url = f"http://{host}:{port}/"
        gateway = {network: gateway_url}

        with open(file, "w+") as f:
            json.dump(gateway, f)

        # Start network
        subprocess.check_call(["starknet-devnet", "--host", host, "--port", str(port)])

    except FileNotFoundError:
        print("")
        print("😰 Could not find starknet-devnet, is it installed? Try with:\n")
        print("   pip install starknet-devnet")
        print("")
