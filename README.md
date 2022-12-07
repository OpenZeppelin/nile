# OpenZeppelin | Nile ⛵

[![Docs](https://img.shields.io/badge/docs-%F0%9F%93%84-blue)](https://docs.openzeppelin.com/nile)
[![Tests and linter](https://github.com/OpenZeppelin/nile/actions/workflows/ci.yml/badge.svg)](https://github.com/OpenZeppelin/nile/actions/workflows/ci.yml)

> _Navigate your [StarkNet](https://www.cairo-lang.org/docs/hello_starknet/index.html) projects written in [Cairo](https://cairo-lang.org)._

## Overview

Nile is a CLI tool to develop or interact with StarkNet projects written in Cairo. It consists of different components for developing, compiling, testing, and deploying your smart contracts and dApps, providing a CLI for executing tasks, and a Runtime Environment (NRE) for scripting. The package is designed to be extensible and very customizable by using plugins.


## Documentation

Check our [documentation site](https://docs.openzeppelin.com/nile) recipes, CLI/API references, and more.

## Quickstart

We will explore the basics of creating a Nile project by using a sample contract. We will test it locally, deploy an account and the contract to a devnet node, and send transactions through the account to the contract.

### Requirements

#### GMP for fastecdsa

Before installing Cairo on your machine, you need to install gmp:

```
sudo apt install -y libgmp3-dev # linux
brew install gmp # mac
```

> **_NOTE:_** If you have any trouble installing gmp on your Apple M1 computer, [here’s a list of potential solutions.](https://github.com/OpenZeppelin/nile/issues/22)

#### Supported Python versions

Some Nile dependencies have specific python version requirements, therefore we recommend using a python version manager like pyenv, and virtual environments to avoid conflicts.

Current supported Python versions are >=3.8 and <3.10.

### Installation

Create a folder for your project and cd into it:

```
mkdir myproject && cd myproject
```

Create a virtualenv and activate it:

```
python3 -m venv env
source env/bin/activate
```

Install Nile:

```
(env): pip install cairo-nile
```

Use `nile init` to quickly set up your development environment:

```
(env): nile init
🗄 Creating project directory tree
⛵️ Nile project ready! Try running:

nile compile
```

### Compiling

Use `nile compile` to compile contracts under the **contracts/** folder by default.

```
(env): nile compile
🤖 Compiling all Cairo contracts in the contracts directory
🔨 Compiling contracts/contract.cairo
✅ Done
```

For a full reference of nile command options, check the [CLI Reference]() section.

### Testing

`nile init` creates a sample Cairo contract and test for you. Check **contracts/contract.cairo** and **tests/test_contract.py** for the source code.

Run pytest to run the test suite against the Smart Contracts:

```
(env): pytest tests/
```

For a more in deep guide on testing with parallelism and coverage, check our [Testing]() guide.


## Contribute

OpenZeppelin Nile exists thanks to its contributors. There are many ways you can participate and help build high quality software. Check out the [contribution](CONTRIBUTING.md) guide!

## License

Nile is released under the MIT License.
