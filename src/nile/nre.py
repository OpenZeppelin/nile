"""nile runtime environment."""
from nile import deployments
from nile.core.account import Account
from nile.core.call_or_invoke import call_or_invoke
from nile.core.compile import compile
from nile.core.deploy import deploy


class NileRuntimeEnvironment:
    """The NileRuntimeEnvironment exposes Nile functionality when running a script."""

    def __init__(self, network="localhost"):
        """Construct NRE object."""
        self.network = network

    def compile(self, contracts):
        """Compile a list of contracts."""
        return compile(contracts)

    def deploy(self, contract, arguments=None, alias=None, overriding_path=None):
        """Deploy a smart contract."""
        if arguments is None:
            arguments = []
        return deploy(contract, arguments, self.network, alias, overriding_path)

    def call(self, contract, method, params=None):
        """Call a view function in a smart contract."""
        if params is None:
            params = []
        return call_or_invoke(contract, "call", method, params, self.network)

    def invoke(self, contract, method, params=None):
        """Invoke a mutable function in a smart contract."""
        if params is None:
            params = []
        return call_or_invoke(contract, "invoke", method, params, self.network)

    def get_deployment(self, contract):
        """Get a deployment by its identifier (address or alias)."""
        return next(deployments.load(contract, self.network))

    def get_or_deploy_account(self, signer):
        """Get or deploy an Account contract."""
        return Account(signer, self.network)
