"""Command to start StarkNet local network."""
import subprocess


def node_command(port: int):
    """Start StarkNet local network."""
    try:
        subprocess.check_call(f"starknet-devnet --port={port}")
    except FileNotFoundError:
        print("")
        print("😰 Could not find starknet-devnet, is it installed? Try with:\n")
        print("   pip install starknet-devnet")
        print("")
