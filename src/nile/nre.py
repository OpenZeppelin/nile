"""nile runtime environment."""
from nile import deployments
from nile.core.account import Account
from nile.core.call_or_invoke import call_or_invoke
from nile.core.compile import compile
from nile.core.declare import declare
from nile.core.deploy import deploy
from nile.core.plugins import get_installed_plugins, skip_click_exit
from nile.utils.get_accounts import get_accounts


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

    def declare(self, contract, alias=None, overriding_path=None):
        """Declare a smart contract class."""
        return declare(contract, self.network, alias)

    def deploy(self, contract, arguments=None, alias=None, overriding_path=None):
        """Deploy a smart contract."""
        return deploy(contract, arguments, self.network, alias, overriding_path)

    def call(self, contract, method, params=None):
        """Call a view function in a smart contract."""
        return str(
            call_or_invoke(contract, "call", method, params, self.network)
        ).split()

    def invoke(self, contract, method, params=None):
        """Invoke a mutable function in a smart contract."""
        return call_or_invoke(contract, "invoke", method, params, self.network)

    def get_deployment(self, identifier):
        """Get a deployment by its identifier (address or alias)."""
        return next(deployments.load(identifier, self.network))

    def get_declaration(self, identifier):
        """Get a declared class by its identifier (class hash or alias)."""
        return next(deployments.load_class(identifier, self.network))

    def get_or_deploy_account(self, signer):
        """Get or deploy an Account contract."""
        return Account(signer, self.network)

    def get_accounts(self):
        """Retrieve and manage deployed accounts."""
        return get_accounts(self.network)
