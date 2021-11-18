"""Command to call or invoke StarkNet smart contracts."""
import os
import subprocess
import json
from dotenv import load_dotenv

from nile import deployments
from nile.common import GATEWAYS

from nile.signer import Signer

pkeys = [123456789987654321, 1] #TODO:remove

def proxy_setup_command(signer, network):
    signer = Signer(pkeys[int(signer)])
    with open("accounts.json", "r") as file:
        accounts = json.load(file)
    #deploy new Account if inexistant
    if (str(signer.public_key) not in accounts):
        signer.index = len(accounts.keys())
        subprocess.run(f"nile deploy Account {signer.public_key} --alias account-{signer.index}", shell=True)
        address, _ = next(deployments.load(f"account-{signer.index}", network))
        #initialize account
        subprocess.run(f"nile invoke account-{signer.index} initialize {address}", shell=True)
        signer.account = address
        accounts[signer.public_key] = {
            "address":address,
            "index":signer.index
        }
        #save accounts
        with open("accounts.json", 'w') as file:
            json.dump(accounts, file)
    else:
        print(f"Account already exists. Proceeding...")
        str_pubkey = str(signer.public_key)
        #load account
        signer.account = accounts[str_pubkey]["address"]
        signer.index = accounts[str_pubkey]["index"]
    return signer

def proxy_command(signer, params, network):
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
        command.extend([param for param in ingested_inputs[0]])
        command.append("--signature")
        command.extend([sig_part for sig_part in ingested_inputs[1]])

    #printed version works
    #print (' '.join(map(str, command)))
    subprocess.check_call(command)
