"""nile common module."""
import json
import os

from nile.common import ACCOUNTS_FILENAME


def register(pubkey, address, index, network):
    """Register a new account."""
    file = f"{network}.{ACCOUNTS_FILENAME}"

    if exists(pubkey, network):
        raise Exception(f"account-{index} already exists in {file}")

    with open(file, "r") as fp:
        accounts = json.load(fp)
        accounts[pubkey] = {"address": address, "index": index}
    with open(file, "w") as file:
        json.dump(accounts, file)


def exists(pubkey, network):
    """Return whether an account exists or not."""
    account = next(load(pubkey, network), None)
    return account is not None


def load(pubkey, network):
    """Load account that matches a pubkey."""
    file = f"{network}.{ACCOUNTS_FILENAME}"

    if not os.path.exists(file):
        with open(file, "w") as fp:
            json.dump({}, fp)

    with open(file) as fp:
        accounts = json.load(fp)
        if pubkey in accounts:
            yield accounts[pubkey]


def current_index(network):
    """Return the length of the accounts. Used as the next index."""
    file = f"{network}.{ACCOUNTS_FILENAME}"

    with open(file) as fp:
        accounts = json.load(fp)
        return len(accounts.keys())
