"""Command to start StarkNet local network."""
import subprocess


def node_command():
    """Start StarkNet local network."""
    subprocess.check_call("starknet-devnet")
