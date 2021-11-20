"""Command to call or invoke StarkNet smart contracts."""
import os
import subprocess

from dotenv import load_dotenv

from nile import accounts, deployments
from nile.common import GATEWAYS
from nile.signer import Signer

load_dotenv()


def proxy_setup_command(signer, network):
    """Deploy an Account contract for the given private key."""
    signer = Signer(int(os.environ[signer]))
    if accounts.exists(str(signer.public_key), network):
        signer_data = next(accounts.load(str(signer.public_key), network))
        signer.account = signer_data["address"]
        signer.index = signer_data["index"]
    else:  # doesn't exist, have to deploy
        signer.index = accounts.current_index(network)
        subprocess.run(
            f"nile deploy Account {signer.public_key} --alias account-{signer.index}",
            shell=True,
        )
        address, _ = next(deployments.load(f"account-{signer.index}", network))
        # initialize account
        subprocess.run(
            f"nile invoke account-{signer.index} initialize {address}", shell=True
        )
        signer.account = address
        accounts.register(signer.public_key, address, signer.index, network)

    return signer


def send_command(signer, contract, method, params, network):
    """Sugared call to a contract passing by an Account contract."""
    address, abi = next(deployments.load(contract, network))
    return proxy_command(signer, [address, method] + list(params), network)


def proxy_command(signer, params, network):
    """Execute a tx going through an Account contract."""
    # params are : to, selector_name, calldata
    signer = proxy_setup_command(signer, network)

    _, abi = next(deployments.load(f"account-{signer.index}", network))

    command = [
        "starknet",
        "invoke",
        "--address",
        signer.account,
        "--abi",
        abi,
        "--function",
        "execute",
    ]

    if network == "mainnet":
        os.environ["STARKNET_NETWORK"] = "alpha"
    else:
        gateway_prefix = "feeder_gateway" if type == "call" else "gateway"
        command.append(f"--{gateway_prefix}_url={GATEWAYS.get(network)}")

    if len(params) > 0:
        command.append("--inputs")
        ingested_inputs = signer.get_inputs(params[0], params[1], params[2:])
        command.extend([str(param) for param in ingested_inputs[0]])
        command.append("--signature")
        command.extend([str(sig_part) for sig_part in ingested_inputs[1]])

    subprocess.check_call(command)
