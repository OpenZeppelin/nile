"""nile runtime environment."""
from nile import deployments
from nile.core.account import Account
from nile.core.call_or_invoke import call_or_invoke
from nile.core.compile import compile
from nile.core.declare import declare
from nile.core.deploy import deploy
from nile.core.plugins import get_installed_plugins, skip_click_exit
from nile.utils.status import status


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

    def declare(
        self,
        contract,
        alias=None,
        overriding_path=None,
        track=False,
        debug=False,
    ):
        """Declare a smart contract class."""
        return declare(contract, self.network, alias, overriding_path, track, debug)

    def deploy(
        self,
        contract,
        arguments=None,
        alias=None,
        overriding_path=None,
        track=False,
        debug=False,
    ):
        """Deploy a smart contract."""
        if arguments is None:
            arguments = []
        return deploy(
            contract,
            arguments,
            self.network,
            alias,
            overriding_path,
            track=track,
            debug=debug,
        )

    def call(self, contract, method, params=None):
        """Call a view function in a smart contract."""
        if params is None:
            params = []
        return call_or_invoke(contract, "call", method, params, self.network)

    def invoke(self, contract, method, params=None, track=False, debug=False):
        """Invoke a mutable function in a smart contract. Return TransactionStatus."""
        if params is None:
            params = []
        return call_or_invoke(
            contract, "invoke", method, params, self.network, track=track, debug=debug
        )

    def get_deployment(self, identifier):
        """Get a deployment by its identifier (address or alias)."""
        return next(deployments.load(identifier, self.network))

    def get_declaration(self, identifier):
        """Get a declared class by its identifier (class hash or alias)."""
        return next(deployments.load_class(identifier, self.network))

    def get_or_deploy_account(self, signer, track=False, debug=False):
        """Get or deploy an Account contract."""
        return Account(signer, self.network, track=False, debug=False)

    def status(self, tx_hash, track=False, debug=False, contracts_file=None):
        """Get/track/debug the status of a transaction."""
        return status(tx_hash, self.network, track, debug, contracts_file)
