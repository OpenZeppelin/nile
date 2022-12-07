# OpenZeppelin | Nile ⛵

[![Docs](https://img.shields.io/badge/docs-%F0%9F%93%84-blue)](https://docs.openzeppelin.com/nile)
[![Tests and linter](https://github.com/OpenZeppelin/nile/actions/workflows/ci.yml/badge.svg)](https://github.com/OpenZeppelin/nile/actions/workflows/ci.yml)

> _Navigate your [StarkNet](https://www.cairo-lang.org/docs/hello_starknet/index.html) projects written in [Cairo](https://cairo-lang.org)._

## Overview

Nile is a CLI tool to develop or interact with StarkNet projects written in Cairo. It consists of different components for developing, compiling, testing, and deploying your smart contracts and dApps, providing a CLI for executing tasks, and a Runtime Environment (NRE) for scripting. The package is designed to be extensible and very customizable by using plugins.

## Installation

> Current supported Python versions are >=3.8 and <3.10.

1. Install `gmp` on your machine (Cairo requirement).

```
sudo apt install -y libgmp3-dev # linux
brew install gmp # mac
```

If you have any trouble installing it on your Apple M1 computer, [here’s a list of potential solutions.](https://github.com/OpenZeppelin/nile/issues/22)


2. Create a folder for your project and cd into it:

```
mkdir myproject && cd myproject
```

3. Create a virtualenv and activate it:

```
python3 -m venv env
source env/bin/activate
```

4. Install Nile:

```
(env): pip install cairo-nile
```

## Quick usage

Use `nile init` to quickly set up your development environment:

```
(env): nile init
🗄 Creating project directory tree
⛵️ Nile project ready! Try running:

nile compile
```

## Documentation

On our official docsite you can find:

- A Quickstart walkthrough with commands examples
- Guides on how to master development with Nile
- Useful script examples
- Plugins list

Check our [documentation site](https://docs.openzeppelin.com/nile) for recipes, CLI/API references, and more.


## Contribute

OpenZeppelin Nile exists thanks to its contributors. There are many ways you can participate and help build high quality software. Check out the [contribution](CONTRIBUTING.md) guide!

## License

Nile is released under the MIT License.
