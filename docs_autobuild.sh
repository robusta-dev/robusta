#!/bin/bash

cd docs && make clean && cd ..
poetry run sphinx-autobuild -a $@ docs docs/_build/html || printf '\n\nError running docs_autobuild. \nMake sure you are using poetry >= 1.1.15. \nCheck out https://docs.robusta.dev/master/extending/platform/docs-contributions.html\n'
