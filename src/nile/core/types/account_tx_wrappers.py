"""Wrappers for transactions with Nile logic."""

import dataclasses
from typing import List, Literal

from nile.core.declare import declare
from nile.core.deploy import deploy_contract


@dataclasses.dataclass
class BaseTxWrapper:
    """Base Wrapper logic."""

    tx: object
    account: object

    async def execute(self):
        """Execute the wrapped transaction."""
        return await self.tx.execute(signer=self.account.signer)

    async def estimate_fee(self):
        """Estimate the fee of the wrapped transaction."""
        return await self.tx.estimate_fee(signer=self.account.signer)

    async def simulate(self):
        """Simulate the wrapped transaction."""
        return await self.tx.simulate(signer=self.account.signer)


@dataclasses.dataclass
class InvokeTxWrapper(BaseTxWrapper):
    """Wrapper for send."""

    watch_mode: Literal["track", "debug"] = None

    async def execute(self):
        """Execute the wrapped transaction."""
        return await self.tx.execute(
            signer=self.account.signer, watch_mode=self.watch_mode
        )


@dataclasses.dataclass
class DeclareTxWrapper(BaseTxWrapper):
    """
    Wrapper for declare.

    Handle registrations and other Nile specific logic.
    """

    alias: str = None
    overriding_path: List[str] = None
    mainnet_token: str = None
    watch_mode: Literal["track", "debug"] = None

    async def execute(self):
        """Execute the wrapped transaction."""
        return await declare(
            transaction=self.tx,
            signer=self.account.signer,
            alias=self.alias,
            overriding_path=self.overriding_path,
            mainnet_token=self.mainnet_token,
            watch_mode=self.watch_mode,
        )


@dataclasses.dataclass
class DeployContractTxWrapper(BaseTxWrapper):
    """
    Wrapper for deploy_contract.

    Handle registrations and other Nile specific logic.
    """

    alias: str = None
    overriding_path: List[str] = None
    watch_mode: Literal["track", "debug"] = None

    async def execute(self):
        """Execute the wrapped transaction."""
        return await deploy_contract(
            transaction=self.tx,
            signer=self.account.signer,
            alias=self.alias,
            overriding_path=self.overriding_path,
            watch_mode=self.watch_mode,
        )


@dataclasses.dataclass
class DeployAccountTxWrapper(BaseTxWrapper):
    """
    Wrapper for deploy_account.

    Handle registrations and other Nile specific logic.
    """

    alias: str = None
    overriding_path: List[str] = None
    watch_mode: Literal["track", "debug"] = None

    async def execute(self):
        """Pending implementation."""
        pass
