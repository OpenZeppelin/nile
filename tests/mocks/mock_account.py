"""Account object mock."""

import os

from nile.common import normalize_number
from nile.core.types.account import Account
from nile.signer import Signer

MOCK_ADDRESS = 0x890


class MockAccount(Account):
    """Mock class."""

    async def __init__(self, signer, network, salt=0, address=MOCK_ADDRESS):
        """Get or deploy an Account contract for the given private key."""
        self.signer = Signer(normalize_number(os.environ[signer]))
        self.alias = signer
        self.network = network
        self.address = address
        self.index = 0
