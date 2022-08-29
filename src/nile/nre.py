"""nile runtime environment."""
from nile import deployments
from nile.core.account import Account
from nile.core.call_or_invoke import call_or_invoke
from nile.core.compile import compile
from nile.core.declare import declare
from nile.core.deploy import deploy
from nile.core.plugins import get_installed_plugins, skip_click_exit


class NileRuntimeEnvironment:
    """The NileRuntimeEnvironment exposes Nile functionality when running a script."""

    def __init__(self, network="localhost"):
        """Construct NRE object."""
        self.network = network
        for name, object in get_installed_plugins().items():
            setattr(self, name, skip_click_exit(object))

    def compile(self, contracts):
        """Compile a list of contracts."""
        return compile(contracts)

    async def declare(self, contract, alias=None, overriding_path=None):
        """Declare a smart contract class."""
        return await declare(contract, self.network, alias)

    async def deploy(self, contract, arguments=None, alias=None, overriding_path=None):
        """Deploy a smart contract."""
        return await deploy(contract, arguments, self.network, alias, overriding_path)

    async def call(self, contract, method, params=None):
        """Call a view function in a smart contract."""
        return await call_or_invoke(contract, "call", method, params, self.network)

    async def invoke(self, contract, method, params=None):
        """Invoke a mutable function in a smart contract."""
        return await call_or_invoke(contract, "invoke", method, params, self.network)

    def get_deployment(self, identifier):
        """Get a deployment by its identifier (address or alias)."""
        return next(deployments.load(identifier, self.network))

    def get_declaration(self, identifier):
        """Get a declared class by its identifier (class hash or alias)."""
        return next(deployments.load_class(identifier, self.network))

    async def get_or_deploy_account(self, signer):
        """Get or deploy an Account contract."""
        return await Account(signer, self.network)
