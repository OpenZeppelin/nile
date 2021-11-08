"""Command to start StarkNet local network."""
import subprocess


def node_command():
    """Start StarkNet local network."""
    try:
        subprocess.check_call("starknet-devnet")
    except FileNotFoundError:
        print("")
        print("😰 Could not find starknet-devnet, is it installed? Try with:\n")
        print("   pip install starknet-devnet")
        print("")
