#!/bin/bash

cd docs && make clean && cd ..
poetry run sphinx-autobuild docs docs/_build/html
