"""nile runtime environment."""
from nile import deployments
from nile.common import is_alias
from nile.core.account import Account
from nile.core.call_or_invoke import call_or_invoke
from nile.core.compile import compile
from nile.core.deploy import deploy
from nile.core.plugins import get_installed_plugins, skip_click_exit
from nile.utils import normalize_number
from nile.utils.get_accounts import get_accounts, get_predeployed_accounts
from nile.utils.get_balance import get_balance
from nile.utils.get_nonce import get_nonce


class NileRuntimeEnvironment:
    """The NileRuntimeEnvironment exposes Nile functionality when running a script."""

    def __init__(self, network="localhost"):
        """Construct NRE object."""
        self.network = network
        for name, object in get_installed_plugins("nre").items():
            setattr(self, name, skip_click_exit(object))

    def compile(self, contracts, cairo_path=None):
        """Compile a list of contracts."""
        return compile(contracts, cairo_path=cairo_path)

    def deploy(
        self,
        contract,
        arguments=None,
        alias=None,
        overriding_path=None,
        abi=None,
        mainnet_token=None,
        watch_mode=None,
    ):
        """Deploy a smart contract."""
        return deploy(
            contract_name=contract,
            arguments=arguments,
            network=self.network,
            alias=alias,
            overriding_path=overriding_path,
            abi=abi,
            mainnet_token=mainnet_token,
            watch_mode=watch_mode,
        )

    def call(self, address_or_alias, method, params=None, abi=None):
        """Call a view function in a smart contract."""
        if not is_alias(address_or_alias):
            address_or_alias = normalize_number(address_or_alias)
        return call_or_invoke(
            address_or_alias, "call", method, params, self.network, abi=abi
        )

    def get_deployment(self, address_or_alias):
        """Get a deployment by its identifier (address or alias)."""
        if not is_alias(address_or_alias):
            address_or_alias = normalize_number(address_or_alias)
        return next(deployments.load(address_or_alias, self.network))

    def get_declaration(self, address_or_alias):
        """Get a declared class by its identifier (class hash or alias)."""
        if not is_alias(address_or_alias):
            address_or_alias = normalize_number(address_or_alias)
        return next(deployments.load_class(address_or_alias, self.network))

    def get_or_deploy_account(self, signer, watch_mode=None):
        """Get or deploy an Account contract."""
        return Account(signer=signer, network=self.network, watch_mode=watch_mode)

    def get_accounts(self, predeployed=False):
        """Retrieve and manage deployed accounts."""
        if not predeployed:
            return get_accounts(self.network)
        else:
            return get_predeployed_accounts(self.network)

    def get_nonce(self, contract_address):
        """Retrieve the nonce for a contract."""
        return get_nonce(contract_address, self.network)

    def get_balance(self, account):
        """Get the Ether balance of an address."""
        return get_balance(account, self.network)
