"""nile runtime environment."""
from nile import deployments
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

    def deploy(self, contract, arguments, alias, overriding_path=None):
        """Deploy a smart contract."""
        return deploy(contract, arguments, self.network, alias, overriding_path)

    def call(self, contract, method, params):
        """Call a view function in a smart contract."""
        return call_or_invoke(contract, "call", method, params, self.network)

    def invoke(self, contract, method, params):
        """Invoke a mutable function in a smart contract."""
        return call_or_invoke(contract, "invoke", method, params, self.network)

    def get_deployment(self, contract):
        """Get a deployment by its identifier (address or alias)."""
        return next(deployments.load(contract, self.network))
