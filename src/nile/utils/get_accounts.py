"""Retrieve and manage deployed accounts."""
import json
import logging

from nile.accounts import current_index
from nile.core.account import Account


def _check_and_return_account(signer, pubkey, network):
    account = Account(signer, network)
    assert str(pubkey) == str(
        account.signer.public_key
    ), "Signer pubkey does not match deployed pubkey"
    return account


def get_accounts(network):
    """Retrieve deployed accounts."""
    try:
        total_accounts = current_index(network)
        logging.info(f"\nTotal accounts: {total_accounts}\n")
    except FileNotFoundError:
        logging.info(f"\nNo deployed accounts detected in {network}\n")
        return

    with open(f"{network}.accounts.json", "r") as f:
        account_data = json.load(f)

    accounts = []
    pubkeys = list(account_data.keys())
    addresses = [i["address"] for i in account_data.values()]
    signers = [i["alias"] for i in account_data.values()]

    for i in range(total_accounts):
        logging.info(f"{i}: {addresses[i]}")

        _account = _check_and_return_account(signers[i], pubkeys[i], network)
        accounts.append(_account)

    logging.info("\n🚀 Successfully retrieved deployed accounts")
    return accounts
