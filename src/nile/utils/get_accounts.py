"""Retrieve and manage deployed accounts."""
import json
import logging

import requests

from nile.accounts import current_index
from nile.common import get_gateways
from nile.core.account import Account
from nile.utils import hex_address, normalize_number

GATEWAYS = get_gateways()

# remove requests info logs coming from urllib3
logging.getLogger("urllib3").setLevel(logging.WARNING)


async def get_accounts(network):
    """Retrieve deployed accounts."""
    try:
        total_accounts = current_index(network)
        logging.info(f"\nTotal registered accounts: {total_accounts}\n")
    except FileNotFoundError:
        print(f"\n❌ No registered accounts detected in {network}.accounts.json")
        print("For more info, see https://github.com/OpenZeppelin/nile#get-accounts\n")
        return

    with open(f"{network}.accounts.json", "r") as f:
        account_data = json.load(f)

    accounts = []
    pubkeys = [normalize_number(i) for i in account_data.keys()]
    addresses = [normalize_number(i["address"]) for i in account_data.values()]
    signers = [i["alias"] for i in account_data.values()]

    for i in range(total_accounts):
        logging.info(f"{i}: {hex_address(addresses[i])}")

        _account = await _check_and_return_account(signers[i], pubkeys[i], network)
        accounts.append(_account)

    logging.info("\n🚀 Successfully retrieved deployed accounts")
    return accounts


async def get_predeployed_accounts(network):
    """Retrieve pre-deployed accounts."""
    endpoint = f"{GATEWAYS.get(network)}/predeployed_accounts"

    try:
        # get the account objects from the rest api
        response = requests.get(endpoint)
        _accounts = response.json()
    except requests.exceptions.MissingSchema:
        logging.error("\n❌ Failed to retrieve gateway from provided network")
        return
    except Exception:
        logging.error("\n❌ Error querying the account from the gateway")
        logging.error("Check you are connected to a starknet-devnet implementation")
        return

    # the account instances from core/account
    accounts = []

    for i in range(len(_accounts)):
        logging.info(f"{i}: {_accounts[i]['address']}")

        predeployed_info = {
            "address": normalize_number(_accounts[i]["address"]),
            "alias": f"account-{i}",
            "index": i,
        }

        _account = await _check_and_return_account(
            normalize_number(_accounts[i]["private_key"]),
            normalize_number(_accounts[i]["public_key"]),
            network,
            predeployed_info,
        )

        accounts.append(_account)

    logging.info("\n🚀 Successfully retrieved pre-deployed accounts")
    return accounts


async def _check_and_return_account(signer, pubkey, network, predeployed_info=None):
    account = await Account(signer, network, predeployed_info=predeployed_info)
    assert (str(pubkey)) == str(
        account.signer.public_key
    ), "Signer pubkey does not match deployed pubkey"
    return account
