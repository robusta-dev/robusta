#!/bin/sh
# Installs everything the docs build needs into this project's virtualenv: the runner with its runtime dependencies from
# the root poetry.lock (autorobusta imports it), then the docs tools from docs/poetry.lock. The docs tools go second
# because myst-parser needs markdown-it-py 3, which the root lock has at 4.
set -e
cd "$(dirname "$0")"
# Both installs go into this project's virtualenv, never an activated one such as the runner's.
unset VIRTUAL_ENV
poetry env use "${PYTHON:-python3.11}" >/dev/null
VIRTUAL_ENV=$(poetry env info --path)
export VIRTUAL_ENV
poetry --directory .. install --only main --extras all
poetry install --no-root
