# OpenZeppelin Nile ⛵

[![Tests and linter](https://github.com/OpenZeppelin/nile/actions/workflows/ci.yml/badge.svg)](https://github.com/OpenZeppelin/nile/actions/workflows/ci.yml)

_Navigate your [StarkNet](https://www.cairo-lang.org/docs/hello_starknet/index.html) projects written in [Cairo](https://cairo-lang.org)._

## Getting started

Create a folder for your project and `cd` into it:

```sh
mkdir myproject
cd myproject
```

Create a [virtualenv](https://docs.python.org/3/library/venv.html) and activate it:

```sh
python3 -m venv env
source env/bin/activate
```

Install `nile`:

```sh
pip install cairo-nile
```

Use `nile` to quickly set up your development environment:

```sh
nile init
...
✨  Cairo successfully installed!
...
🗄  Creating project directory tree
⛵️ Nile project ready! Try running:
```

`nile init` builds the project structure by:

- Creating directories for `contracts` and `tests`.
- Populating these directories with test modules.
- Generating a `.env` to store private key aliases.
- Setting up a `node.json` for initializing a local node.

## Usage

### `node`

Run a local [`starknet-devnet`](https://github.com/Shard-Labs/starknet-devnet/) node:

```text
nile node [--host HOST] [--port PORT] [--seed SEED] [--lite_mode]

optional arguments:
--host HOST         Specify the address to listen at; defaults to
                    127.0.0.1 (use the address the program outputs on
                    start)
--port PORT         Specify the port to listen at; defaults to 5050
--seed SEED         Specify the seed for randomness of accounts to be
                    deployed
--lite-mode         Applies all lite-mode optimizations by disabling
                    features such as block hash and deploy hash
                    calculation
```

```text
nile node

Account #0
Address: 0x877b050406a54adb5940227e51265a201e467e520ca85dc7f024abd03dcc61
Public key: 0x256b8dc218586160ef80d3454a7cd51046271fbf091bd6779e3513304f22156
Private key: 0xb204ff062d85674b467789f07826bb2

...

Initial balance of each account: 1000000000000000000000 WEI
Seed to replicate this account sequence: 2128506880
WARNING: Use these accounts and their keys ONLY for local testing. DO NOT use them on mainnet or other live networks because you will LOSE FUNDS.

 * Listening on http://127.0.0.1:5050/ (Press CTRL+C to quit)
```

### `compile`

Compile Cairo contracts. Compilation artifacts are written into the `artifacts/` directory.

```txt
nile compile [PATH_TO_CONTRACT] [--directory DIRECTORY] [--disable-hint-validation]
```

For example:

```sh
nile compile # compiles all contracts under contracts/
nile compile --directory my_contracts # compiles all contracts under my_contracts/
nile compile contracts/MyContract.cairo # compiles single contract
nile compile contracts/MyContract.cairo --disable-hint-validation # compiles single contract with unwhitelisted hints
```

As of cairo-lang v0.8.0, account contracts (contracts with the `__execute__` method) must be compiled with the `--account_contract` flag. Nile automatically inserts the flag if the contract's name ends with `Account` i.e. Account.cairo, EthAccount.cairo. Otherwise, the flag must be included by the user.

```sh
nile compile contracts/NewAccountType.cairo --account_contract # compiles account contract
```

Example output:

```sh
$ nile compile
Creating artifacts/abis/ to store compilation artifacts
🤖 Compiling all Cairo contracts in the contracts/ directory
🔨 Compiling contracts/Account.cairo
🔨 Compiling contracts/Initializable.cairo
🔨 Compiling contracts/Ownable.cairo
✅ Done
```

### `deploy`

> NOTICE: Calling this method with `--ignore_account` is discouraged and will be removed soon, as StarkNet will make deployments from accounts mandatory.

> Token for deployments to Alpha Mainnet can be set with the `--token` option.

```txt
nile deploy <private_key_alias> <contract> [--alias ALIAS] [--network NETWORK] [--track | --debug]
```

For example:

```sh
nile deploy <private_key_alias> contract --alias my_contract

🚀 Deploying contract
⏳ ️Deployment of contract successfully sent at 0x07ec10eb0758f7b1bc5aed0d5b4d30db0ab3c087eba85d60858be46c1a5e4680
🧾 Transaction hash: 0x79e596c39cfec555f2d17253d043a0defd64a851a268b68c13811f328baf123
📦 Registering deployment as my_contract in localhost.deployments.txt
```

A few things to note here:

1. `nile deploy <contract_name>` looks for an artifact with the same name.
2. This creates or updates the `localhost.deployments.txt` file storing all data related to deployments.
3. The `--ignore_account` flag deploys without using the account (DEPRECATED).
4. The `--alias` parameter creates a unique identifier for future interactions, if no alias is set then the contract's address can be used as identifier.
5. The `--deployer_address` parameter lets you specify the deployer contract address if needed.
6. By default Nile works on local, but you can use the `--network` parameter to interact with `mainnet`, `goerli`, `goerli2`, `integration`, and the default `localhost`.
7. By default, the ABI corresponding to the contract will be registered with the deployment. To register a different ABI file, use the `--abi` parameter.
8. `--track` and `--debug` flags can be used to watch the status of the deployment transaction. See `status` below for a complete description.

### `setup`

Deploy an Account associated with a given private key.

To avoid accidentally leaking private keys, this command takes an alias instead of the actual private key. This alias is associated with an environmental variable of the same name, whose value is the actual private key.

```sh
nile setup <private_key_alias> [--salt SALT] [--max_fee MAX_FEE] [--network NETWORK]

🚀 Deploying Account
⏳ ️Deployment of Account successfully sent at 0x07db6b52c8ab888183277bc6411c400136fe566c0eebfb96fffa559b2e60e794
🧾 Transaction hash: 0x17
📦 Registering deployment as account-0 in localhost.deployments.txt
```

A few things to note here:

- This is a counterfactual deployment, meaning the deployed account pays for its own deployment. You can use [`nile counterfactual-address`](#counterfactual-address) to predict the account address and send the necessary funds beforehand.
- `nile setup <private_key_alias>` looks for an environment variable with the name of the private key alias.
- This creates or updates `localhost.accounts.json` file storing all data related to account management.
- The creates or updates `localhost.deployments.txt` file storing all data related to deployments.
- `--track` and `--debug` flags can be used to watch the status of the account deployment transaction. See `status` below for a complete description.

### `counterfactual-address`

Precompute the deployment address of an Account contract, for a given signer and salt. If not provided, `salt` defaults to `0`.

```sh
nile counterfactual-address <private_key_alias> [--salt SALT]
```

For example:

```sh
nile counterfactual-address <private_key_alias> --salt 123

0x00193c9bf3f66f556b40f0e95dffdd07db2cd6b10552a75048b71550049d1246
```

### `send`

Execute a transaction through the `Account` associated with the private key provided. The syntax is:

```sh
nile send <private_key_alias> <contract_identifier> <method> [PARAM_1, PARAM2...] [--track | --debug]
```

For example:

```sh
nile send <private_key_alias> ownable0 transfer_ownership 0x07db6...60e794

Invoke transaction was sent.
Contract address: 0x07db6b52c8ab888183277bc6411c400136fe566c0eebfb96fffa559b2e60e794
Transaction hash: 0x1c
```

Some things to note:

- This sends the transaction to the network by default, but you can use the `--estimate_fee` flag to estimate the fee without sending the transaction, or the `--simulate` flag to get a traceback of the simulated execution.
- `max_fee` defaults to `0`. Add `--max_fee <max_fee>` to set the maximum fee for the transaction.
- `network` defaults to the `localhost`. Add `--network <network>` to change the network for the transaction.
- `--track` and `--debug` flags can be used to watch the status of the transaction. See `status` below for a complete description.

### `declare`

> Token for declarations to Alpha Mainnet can be set with the `--token` option.

Very similar to `send`, but for declaring a contract based on its name through an account.

```sh
nile declare <private_key_alias> contract --alias my_contract

🚀 Declaring contract
⏳ Successfully sent declaration of contract as 0x07ec10eb0758f7b1bc5aed0d5b4d30db0ab3c087eba85d60858be46c1a5e4680
🧾 Transaction hash: 0x7222604b048632326f6a016ccb16fbdea7e926cd9e2354544800667a970aee4
📦 Registering declaration as my_contract in localhost.declarations.txt
```

A few things to notice here:

- `nile declare <private_key_alias> <contract_name>` looks for an artifact with name `<contract_name>`.
- This creates or updates a `localhost.declarations.txt` file storing all data related to your declarations.
- The `--alias` parameter lets you create a unique identifier for future interactions, if no alias is set then the contract's address can be used as identifier.
- By default Nile works on local, but you can use the `--network` parameter to interact with `mainnet`, `goerli`, `goerli2`, `integration`, and the default `localhost`.
- `--track` and `--debug` flags can be used to watch the status of the declaration transaction. See `status` below for a complete description.

### `call`

Using `call`, we can perform read operations against our local node or the specified public network. The syntax is:

```sh
nile call <contract_identifier> <method> [PARAM_1, PARAM2...]
```

Where `<contract_identifier>` is either our contract address or alias, as defined on `deploy`.

```sh
nile call my_contract get_balance

1
```

Please note:

- `network` defaults to the `localhost`. Add `--network <network>` to change the network for the transaction.

### `run`

Execute a script in the context of Nile. The script must implement an asynchronous `run(nre)` function to receive a `NileRuntimeEnvironment` object exposing Nile's scripting API.

```python
# path/to/script.py

async def run(nre):
    address, abi = await nre.deploy("contract", alias="my_contract")
    print(abi, address)
```

Then run the script:

```sh
nile run path/to/script.py
```

Please note:

- `localhost` is the default network. Add `--network <network>` to change the network for the script

### `clean`

Deletes the `artifacts/` directory for a fresh start ❄️

```sh
nile clean

🚮 Deleting localhost.deployments.txt
🚮 Deleting artifacts directory
✨ Workspace clean, keep going!
```

### `version`

Print out the Nile version

```sh
nile version
```

### `status`

Prints the current status of a transaction.

```txt
nile status <transaction_hash> [--contracts_file FILE] [--network NETWORK] [--track | --debug]
```

#### `--track`, `-t` flag

In case of pending transaction states, continue probing the network. Here in the case of a successful transaction.

```sh
nile status -t <transaction_hash>
⏳ Querying the network for transaction status...
🕒 Transaction status: NOT_RECEIVED. Trying again in a moment...
🕒 Transaction status: RECEIVED. Trying again in a moment...
🕒 Transaction status: PENDING. Trying again in a moment...
✅ Transaction status: ACCEPTED_ON_L2. No error in transaction.
```

#### `--debug`, `-d` flag

Use locally available contracts to make error messages from rejected transactions more explicit.
Note: Implies `--track`.

For example, this transaction returns the very cryptic error message:
`An ASSERT_EQ instruction failed: 0 != 1.`

```sh
starknet tx_status \
  --hash 0x57d2d844923f9fe5ef54ed7084df61f926b9a2a24eb5d7e46c8f6dbcd4baafe \
  --error_message

[...]
Error in the called contract (0x5bf05eece944b360ff0098eb9288e49bd0007e5a9ed80aefcb740e680e67ea4):
Error at pc=0:1360:
An ASSERT_EQ instruction failed: 0 != 1.
Cairo traceback (most recent call last):
Unknown location (pc=0:1384)
Unknown location (pc=0:1369)
```

This can be made more explicit with:

```sh
nile status -d 0x57d2d844923f9fe5ef54ed7084df61f926b9a2a24eb5d7e46c8f6dbcd4baafe

⏳ Querying the network for transaction status...
❌ Transaction status: REJECTED.
🧾 Found contracts: ['0x05bf05eece944b360ff0098eb9288e49bd0007e5a9ed80aefcb740e680e67ea4:artifacts/Evaluator.json']
⏳ Querying the network with contracts...
🧾 Error message:

[...]
Error in the called contract (0x5bf05eece944b360ff0098eb9288e49bd0007e5a9ed80aefcb740e680e67ea4):
[path_to_file]:179:5: Error at pc=0:1360:
    assert permission = 1
    ^*******************^
An ASSERT_EQ instruction failed: 0 != 1.
Cairo traceback (most recent call last):
[path_to_file]:184:6
func set_teacher{
     ^*********^
[path_to_file]:189:5
    only_teacher()
    ^************^
```

Finally, the command will use the local `network.deployments.txt` files to fetch the available contracts.
However, it is also possible to override this by passing a `CONTRACTS_FILE` argument, formatted as:

```txt
CONTRACT_ADDRESS1:PATH_TO_COMPILED_CONTRACT1[:ALIAS1].json
CONTRACT_ADDRESS2:PATH_TO_COMPILED_CONTRACT2[:ALIAS1].json
...
```

### `debug`

Alias for `nile status --debug`

```sh
nile debug <transaction_hash> [--contracts_file FILE] [--network NETWORK]
```

### `get-accounts`

Retrieves a list of ready-to-use accounts which allows for easy scripting integration. Before using `get-accounts`:

1. store private keys in a `.env`

    ```txt
    PRIVATE_KEY_ALIAS_1=286426666527820764590699050992975838532
    PRIVATE_KEY_ALIAS_2=263637040172279991633704324379452721903
    PRIVATE_KEY_ALIAS_3=325047780196174231475632140485641889884
    ```

2. deploy accounts with the keys therefrom like this:

    ```bash
    nile setup PRIVATE_KEY_ALIAS_1
    ...
    nile setup PRIVATE_KEY_ALIAS_2
    ...
    nile setup PRIVATE_KEY_ALIAS_3
    ...
    ```

Next, write a script and call `get-accounts` to retrieve and use the deployed accounts.

```python
async def run(nre):

    # fetch the list of deployed accounts
    accounts = await nre.get_accounts()

    # then
    await accounts[0].send(...)

    # or
    alice, bob, *_ = accounts
    await alice.send(...)
    await bob.send(...)
```

> Please note that the list of accounts includes only those that exist in the local `<network>.accounts.json` file. In a recent release we added a flag to the command, to get predeployed accounts if the network you are connected to is a [starknet-devnet](https://github.com/Shard-Labs/starknet-devnet) instance.

### `get-accounts --predeployed (only starknet-devnet)`

This flag retrieves the predeployed accounts if the network you are connecting to is a [starknet-devnet](https://github.com/Shard-Labs/starknet-devnet) instance.

You can use it either from the cli:

```sh
nile get-accounts --predeployed
```

Or from the nile runtime environment for scripting:

```python
async def run(nre):

    # fetch the list of pre-deployed accounts from devnet
    accounts = await nre.get_accounts(predeployed=True)

    # then
    await accounts[0].send(...)

    # or
    alice, bob, *_ = accounts
    await alice.send(...)
    await bob.send(...)
```

### `get-balance`

Retrieves the Ether balance for a given contract address.

```sh
nile get-balance <contract_address> [--network NETWORK]

nile get-balance 0x053edde5384e39bad137d3c4130c708fb96ee28a4c80bf28049c486d3f36992e
🕵️  0x053ed...6992e balance is:
💰 4444.555501003 gwei
```

### `get-nonce`

Retrieves the nonce for the given contract address (usually an account).

```sh
nile get-nonce <contract_address>
```

### `get_declaration` (NRE only)

Return the hash of a declared class. This can be useful in scenarios where a contract class is already declared with an alias prior to running a script.

```python
async def run(nre):
    predeclared_class = await nre.get_declaration("alias")
```

> Note that this command is only available in the context of scripting in the Nile Runtime Environment.

## Short string literals

From [cairo-lang docs](https://www.cairo-lang.org/docs/how_cairo_works/consts.html#short-string-literals): A short string is a string whose length is at most 31 characters, and therefore can fit into a single field element.

In Nile, arguments to contract calls (calldata) that are neither int nor hex, are treated as short strings and converted automatically to the corresponding felt representation. Because of this, you can run the following from the CLI:

```sh
nile deploy MyToken 'MyToken name' 'MyToken symbol' (...)
```

And this is equivalent to passing the felt representation directly like this:

```sh
nile deploy MyToken 0x4d79546f6b656e206e616d65 0x4d79546f6b656e2073796d626f6c (...)
```

Note that if you want to pass the token name as a hex or an int, you need to provide the felt representation directly because these values are not interpreted as short strings. You can open a python terminal, and import and use the `str_to_felt` util like this:

```python
>>> from nile.utils import str_to_felt
>>>
>>> str_to_felt('any string')
460107418789485453340263
```

## Extending Nile with plugins

Nile can extend its CLI and `NileRuntimeEnvironment` functionalities through plugins. For developing plugins, you can fork [this example template](https://github.com/franalgaba/nile-plugin-example) and implement your desired functionality with the provided instructions.

### How it works

This implementation takes advantage of the native extensibility features of [Click](https://click.palletsprojects.com/). By using Click and leveraging Python [entry points](https://packaging.python.org/en/latest/specifications/entry-points/), we have a simple manner of handling extensions natively in Python environments through dependencies. The plugin implementation on Nile looks for specific Python entry point constraints for adding commands to either the CLI or NRE.

In order for this implementation to be functional, the plugin developer must follow some guidelines:

1. Use Click if the plugin provides a CLI command:

   ```python
   # First, import click dependency
   import click

   # Decorate the method that will be the command name with `click.command`
   @click.command()
   # Custom parameters can be added as defined in `click`: https://click.palletsprojects.com/en/7.x/options/
   def greet():
       """
       Plugin CLI command that does something.
       """
       # Done! Now implement the custom functionality in the command
       click.echo("Hello Nile!")
   ```

2. Define the plugin entry points (in this case by using the Poetry plugins feature in the `pyproject.toml` file):

   ```sh
   # We need to specify that Click commands are entry points in the group `nile_plugins`
   [tool.poetry.plugins."nile_plugins.cli"]
   # <command_name> = <package_method_location>
   "greet" = "nile_greet.main.greet"
   ```

3. Optionally specify plugin entry points for `NileRuntimeEnvironment`. This doesn't require implementing a Click command (remove the cli entry points if not needed):

   ```sh
   [tool.poetry.plugins."nile_plugins.cli"]
   "greet" = "nile_greet.main.greet"

   [tool.poetry.plugins."nile_plugins.nre"]
   "greet" = "nile_greet.nre.greet"
   ```

4. Done! For a better understanding of python entry points through setuptools, [check this documentation](https://setuptools.pypa.io/en/latest/userguide/entry_point.html#entry-points-for-plugins).

How to decide if I want to use a plugin or not? Just install / uninstall the plugin dependency from your project :smile:

Using both cli and nre entry points under the nile_plugins group allows the development of powerful plugins which are easily integrated.

## Contribute

OpenZeppelin Nile exists thanks to its contributors. There are many ways you can participate and help build high quality software. Check out the [contribution](CONTRIBUTING.md) guide!

## Hacking on Nile

Nile uses tox to manage development tasks. Here are some hints to play with the source code:

- Install a development version of the package with `python -m pip install .`
- Install tox for development tasks with `python -m pip install tox`
- Get a list of available tasks with `tox -av`
- Build the package with `tox -e build`
- Format all files with `tox -e format`
- Check files formatting with `tox -e lint`

### Testing

To run tests:

- Install testing dependencies with `python -m pip install .[testing]`
- Run all tests with `tox`
- Run unit tests only with `tox -e unit`
- To run a specific set of tests, point to a module and/or function, e.g. `tox tests/test_module.py::test_function`
- Other `pytest` flags must be preceded by `--`, e.g. `tox -- --pdb` to runtests in debug mode

## License

Nile is released under the MIT License.
