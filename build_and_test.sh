#!/bin/bash
set -e

# Color variables
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Function for colored echo
cecho() {
    echo -e "${GREEN}👉 $1${NC}"
}

FAST_MODE=false
for arg in "$@"; do
    if [ "$arg" = "--fast-mode" ]; then
        FAST_MODE=true
        break
    fi
done

if [ "$FAST_MODE" = false ]; then
    cecho "Installing test dependencies"
    poetry install --extras=all

    cecho "Building robusta image to test"
    OUTPUT=$(skaffold build --quiet -o '{{(index .Builds 0).Tag }}' 2>&1) || {
        cecho "Error running 'skaffold build' - try running standalone for more info."
        cecho "Tip: if skaffold shows authentication errors, you need to either change the repo or run 'gcloud auth configure-docker us-central1-docker.pkg.dev'"
        echo "$OUTPUT"
        exit 1
    }
    TAG="$OUTPUT"
    echo "$TAG" > tests/last_used_tag.txt
else
    if [ ! -f tests/last_used_tag.txt ]; then
        cecho "Error: --fast-mode was used before running the script in normal mode."
        cecho "Please run the script without --fast-mode first to generate the necessary files."
        exit 1
    fi
    TAG=$(cat tests/last_used_tag.txt)
fi

# Removing --fast-mode from the arguments
args=()
for arg in "$@"; do
    if [ "$arg" != "--fast-mode" ]; then
        args+=("$arg")
    fi
done

# Add --no-delete-cluster if --fast-mode is set
if [ "$FAST_MODE" = true ]; then
    args+=("--no-delete-cluster")
fi

CMD="poetry run pytest -s -rsx --image=\"$TAG\" ${args[*]}"
cecho "Running tests with pytest: $CMD"
# -o log_cli=true --capture=tee-sys
cecho "To see logging output from tests themselves, run with --log-cli-level=DEBUG or --log-cli-level=INFO"
cecho "To see more output from pytest itself, run with --verbose"
eval $CMD
