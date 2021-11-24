#!/bin/bash

echo "installing test dependencies"
poetry install --extras=all
poetry run pip install git+https://github.com/astanin/python-tabulate.git@b2c26bcb70e497f674b38aa7e29de12c0123708a#egg=tabulate

echo "building robusta image to test"
TAG=$(skaffold build --quiet -o '{{(index .Builds 0).Tag }}')

echo "now testing: $TAG"
poetry run pytest -s --image="$TAG"
