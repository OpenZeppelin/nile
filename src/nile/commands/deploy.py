"""Command to deploy StarkNet smart contracts."""
import os
import subprocess

GATEWAYS = {"localhost": "http://localhost:5000/"}


def deploy_command(artifact, network):
    """Deploy StarkNet smart contracts."""
    print(f"🚀 Deploying {artifact}")

    params = ["starknet", "deploy", "--contract", artifact]

    if network == "mainnet":
        os.environ["STARKNET_NETWORK"] = "alpha"
    else:
        params.append(f"--gateway_url={GATEWAYS.get(network)}")

    subprocess.check_call(params)
    print(f"🌕 {get_contract_name(artifact)} successfully deployed!")


def get_contract_name(artifact):
    """Get the contract name from an artifact."""
    base = os.path.basename(artifact)
    return os.path.splitext(base)[0]
