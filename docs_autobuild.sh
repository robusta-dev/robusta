#!/bin/bash

cd docs && make clean && cd ..
poetry run sphinx-autobuild docs docs/_build/html || printf '\n\nError running docs_autobuild. \nMake sure you are using poetry >= 1.1.15. \nCheck out https://docs.robusta.dev/master/developer-guide/platform/docs-contributions.html\n'
