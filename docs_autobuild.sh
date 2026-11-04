#!/bin/bash
set -e
# poetry run below must use the docs project's virtualenv, not an activated one.
unset VIRTUAL_ENV

docs/install.sh
cd docs
poetry run make clean
poetry run sphinx-autobuild -a $@ . _build/html || printf '\n\nError running docs_autobuild. \nMake sure you are using poetry >= 1.1.15. \nCheck out https://docs.robusta.dev/master/extending/platform/docs-contributions.html\n'
