"""Starknet Devnet integration helpers"""
import json
import requests
import logging

from nile.core.account import Account
from nile.common import get_gateway


GATEWAYS = get_gateway()


def get_predeployed_accounts(network):
    """Retrieve pre-deployed accounts."""
    endpoint = f"{GATEWAYS.get(network)}/predeployed_accounts"

    try:
        response = requests.get(endpoint)
        # get the account objects from the rest api
        _accounts = response.json()
    except requests.exceptions.MissingSchema:
        print(f"\n❌ Failed to retrieve gateway from provided network")
        return
    except Exception:
        print(f"\n❌ Error querying the account from the gateway.")
        print(f"Check you are connected to a starknet-devnet implementation.")
        return

    # get the account objects from the rest api
    _accounts = response.json()

    # the account instances from core/account
    accounts = []

    for i in range(len(_accounts)):
        logging.info(f"{i}: {_accounts[i]['address']}")

        predeployed_info = {
          "address": int(_accounts[i]['address'], 16),
          "alias": f"account-{i}",
          "index": i
        }

        _account = _check_and_return_account(
          _accounts[i]["private_key"],
          _accounts[i]["public_key"],
          predeployed_info,
          network
        )

        accounts.append(_account)

    logging.info("\n🚀 Successfully retrieved pre-deployed accounts")
    return accounts


def _check_and_return_account(signer, pubkey, predeployed_info, network):
    account = Account(signer, network, predeployed_info)
    assert int(pubkey, 16) == account.signer.public_key, "Signer pubkey does not match deployed pubkey"
    return account
