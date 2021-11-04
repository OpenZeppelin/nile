"""Command to deploy StarkNet smart contracts."""
import os
import re
import subprocess

GATEWAYS = {"localhost": "http://localhost:5000/"}
DEPLOYMENTS_FILENAME = "deployments.txt"


def deploy_command(artifact, network):
    """Deploy StarkNet smart contracts."""
    contract = get_contract_name(artifact)
    print(f"🚀 Deploying {contract}")

    params = ["starknet", "deploy", "--contract", artifact]

    if network == "mainnet":
        os.environ["STARKNET_NETWORK"] = "alpha"
    else:
        params.append(f"--gateway_url={GATEWAYS.get(network)}")

    ouput = subprocess.check_output(params)
    address = re.findall("0x[\\da-f]{64}", str(ouput))[0]

    print(f"🌕 {contract} successfully deployed to {address}")

    with open(f"{network}.{DEPLOYMENTS_FILENAME}", "a") as fp:
        print(
            f"📦 Registering {contract} deployment in {network}.{DEPLOYMENTS_FILENAME}"
        )
        fp.write(f"{address}:{artifact}\n")


def get_contract_name(artifact):
    """Get the contract name from an artifact."""
    base = os.path.basename(artifact)
    return os.path.splitext(base)[0]
