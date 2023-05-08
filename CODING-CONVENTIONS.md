# Coding Conventions

The following guidelines apply to code contributions to the Robusta engine itself.

## Formatting

Robusta uses [Black](https://github.com/psf/black) and [ISort](https://pycqa.github.io/isort/) to automatically format code. Please set up Black prior so that all your contributions to Robusta will be formatted properly.

For instructions on using those tools with your IDE, see:

- [Black and ISort for VSCode](https://cereblanco.medium.com/setup-black-and-isort-in-vscode-514804590bf9)
- [Black and ISort for PyCharm](https://johschmidt42.medium.com/automate-linting-formatting-in-pycharm-with-your-favourite-tools-de03e856ee17)

## Linting

Robusta uses [Flake8](https://flake8.pycqa.org/en/latest/) and [PyRight](https://github.com/microsoft/pyright) for code linting and type checking. Please set up Flake8 and PyRight prior so that all your contributions to Robusta will be linted properly.

For instructions on using Flake8 and PyRight tools with VSCode:

- [Flake8 for VSCode](https://code.visualstudio.com/docs/python/linting)
- [PyRight for VSCode](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)

For instructions on using Flake8 and PyRight tools with PyCharm, see:

- [Installing third-party tools in PyCharm](https://www.jetbrains.com/help/pycharm/configuring-third-party-tools.html#remote-ext-tools)

## Pre-Commit Hooks

Robusta uses [pre-commit](https://pre-commit.com/) to run Black, ISort, Flake8 and PyRight (and some other minor hooks) before each commit.

To do so, install Robusta's dependencies with `cd src/ && poetry install` and then install the hook by running `pre-commit install`

## Data classes

Use `pydantic.BaseModel` instead of Python `dataclasses` when possible. Pydantic performs data validation whereas Python `dataclasses` just reduce boilerplate code like defining `__init__()`

## Imports

Use absolute imports whenever possible. For example, instead of `from . import foo`, use `from robusta import foo`

To help with that, pre-commit hook will automatically fix relative imports to absolute imports.
