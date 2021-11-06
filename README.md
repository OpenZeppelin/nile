# OpenZeppelin Nile ⛵

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
✅ Dependencies successfully installed
🗄  Creating project directory tree
⛵️ Nile project ready! Try running:
```
This command creates the project directory structure and installs `cairo-lang`, `starknet-devnet`, `pytest`, and `pytest-asyncio` for you. The template includes a makefile to build the project (`make build`) and run tests (`make test`).

## Usage
### `node`

Run a local [`starknet-devnet`](https://github.com/Shard-Labs/starknet-devnet/) node:

```sh
nile node

 * Serving Flask app 'starknet_devnet.server' (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://localhost:5000/ (Press CTRL+C to quit)
```

### `compile`

Compile Cairo contracts. Compilation articacts are written into the `artifacts/` directory.

```sh
nile compile # compiles all contracts under contracts/
nile compile contracts/MyContract.cairo # compiles single contract
```
Example output:
```
$ nile compile
Creating artifacts/abis/ to store compilation artifacts
🤖 Compiling all Cairo contracts in the contracts/ directory
🔨 Compiling contracts/Account.cairo
🔨 Compiling contracts/Initializable.cairo
🔨 Compiling contracts/Ownable.cairo
✅ Done
```

### `deploy`
```sh
nile deploy contract --alias my_contract

🚀 Deploying contract
🌕 artifacts/contract.json successfully deployed to 0x07ec10eb0758f7b1bc5aed0d5b4d30db0ab3c087eba85d60858be46c1a5e4680
📦 Registering deployment as my_contract in localhost.deployments.txt
```

A few things to notice here:

1. `nile deploy <contract_name>` looks for an artifact with the same name
2. This created a `localhost.deployments.txt` file storing all data related to my deployment
3. The `--alias` parameter lets me create an unique identifier for future interactions, if no alias is set then the contract's address can be used as identifier
4. By default Nile works on local, but you can pass `--network mainnet` to deploy directly to a public chain! Notice that `mainnet` refers to StarkNet main chain, that's settled on Goerli testnet of Ethereum ([mainnet deployment this month!](https://medium.com/starkware/starknet-alpha-is-coming-to-mainnet-b825829eaf32))

### `call` and `invoke`
Using `call` and `invoke`, we can perform read and write operations against our local node (or public one using the `--network mainnet` parameter). The syntax is:

```
nile <command> <contract_identifier> <contract_method> [PARAM_1, PARAM2...]
```

Where `<command>` is either `call` or `invoke` and `<contract_identifier>` is either our contract address or alias, as defined on `deploy`.

```sh
nile invoke my_contract increase_balance 1

Invoke transaction was sent.
Contract address: 0x07ec10eb0758f7b1bc5aed0d5b4d30db0ab3c087eba85d60858be46c1a5e4680
Transaction hash: 0x1
```

```sh
nile call my_contract get_balance

1
```

### `clean`
Deletes the `artifacts/` directory for a fresh start ❄️

```sh
nile clean

🚮 Deleting localhost.deployments.txt
🚮 Deleting artifacts directory
✨ Workspace clean, keep going!
```

### `install`
Install the latest version of the Cairo language and the starknet-devnet local node.

```sh
nile install
```

### `version`
Print out the Nile version

```sh
nile version
```

## Hacking on Nile

Nile uses tox to manage development tasks, you can get a list of
available task with `tox -av`.

 * Install a development version of the package with `python -m pip install .`
 * Run tests with `tox`
 * Build the package with `tox -e build`
 * Format all files with `tox -e format`
 * Check files formatting with `tox -e lint`


## License
Nile is released under the MIT License.
