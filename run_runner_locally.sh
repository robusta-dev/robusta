#!/bin/bash
set -e

# IMPORTANT: this script was tested with poetry 1.4.2
# Run `poetry self update 1.4.2` or try other versions at your own risk!

FAST_MODE=0
for arg in "$@"
do
    if [ "$arg" == "--fast-mode" ]; then
        FAST_MODE=1
        echo "Fast mode enabled"
        break
    fi
done

# Settings you might want to change
export PYTHON_BINARY=python3.9
export PORT=6000  # if you change this, update port_mapping in mirrord.json too
export LOG_LEVEL=INFO
export TRACE_INCOMING_REQUESTS=false

# Internal constants
export RED='\033[0;31m'
export NC='\033[0m' # No Color

# Check if Python 3.9 or higher is installed
if ! $PYTHON_BINARY -c "import sys; exit(not (sys.version_info.major == 3 and sys.version_info.minor >= 9))"; then
  echo -e "${RED}Error: Python 3.9 or higher is not installed or was not run\n${NC}"
  echo "You are using $(PYTHON_BINARY --version) located at $(which $PYTHON_BINARY)"
  echo "To change your Python version, edit the PYTHON_BINARY variable at the top of this script"
  exit 1
fi

# Check if mirrord is installed globally
if ! command -v mirrord &> /dev/null
then
    echo -e "${RED}Mirrord is not installed globally. Follow the guide here to install it: https://github.com/metalbear-co/mirrord?tab=readme-ov-file#cli-tool${NC}"
    exit 1
fi

# Check if Poetry is installed globally
if ! command -v poetry &> /dev/null
then
    echo -e "${RED}Poetry is not installed globally. Make sure the 'poetry' command works${NC}"
    exit 1
fi

echo "Python 3.9+ and Poetry are installed."
echo "Now setting up Robusta"

poetry env use $PYTHON_BINARY
if [ $FAST_MODE -eq 0 ]; then
  poetry install --extras=all
  echo "All dependencies installed"
fi

echo "Setting up local runner environment"
mkdir -p deployment/playbooks/defaults
ln -fs "$(pwd)/playbooks/robusta_playbooks/" ./deployment/playbooks/defaults
ln -fs "$(pwd)/playbooks/pyproject.toml" ./deployment/playbooks/defaults

echo "Checking if runner can listen on port ${PORT}"
if lsof -Pi :${PORT} -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${RED}Error: Port ${PORT} is already in use. Free up the port, or edit this script and change \$PORT. Exiting.${NC}"
    exit 1
fi

echo "Checking for active_playbooks.yaml"
# warning: this doesn't actually run independent of the cluster - e.g. scheduler dal uses cluster state
if [ ! -f "$PWD/deployment/playbooks/active_playbooks.yaml" ]; then
  echo -e "${RED}Error: You need an active_playbooks.yaml to run Robusta locally!${NC}"
  echo "This file must be located at ./deployment/playbooks/active_playboks.yaml"
  echo "You can fix by extracting this file from an existing cluster with Robusta. Run:"
  echo -e "\tkubectl get secret robusta-playbooks-config-secret -o jsonpath='{.data.active_playbooks\.yaml}'  | base64 --decode > ./deployment/playbooks/active_playbooks.yaml"
  echo -e "${RED}After extracting active_playbooks.yaml from your cluster, you MUST change the global_config.cluster_name in it to something else!!!!!${NC}"
  exit 1
fi

if [ $FAST_MODE -eq 0 ]; then
  echo "Installing builtin playbooks"
  poetry run python3 -m pip install -e ./deployment/playbooks/defaults
fi

export PLAYBOOKS_CONFIG_FILE_PATH=./deployment/playbooks/active_playbooks.yaml
export INTERNAL_PLAYBOOKS_ROOT=./src/robusta/core/playbooks/internal
export PLAYBOOKS_ROOT=./deployment/playbooks
export REPO_LOCAL_BASE_DIR=./deployment/git_playbooks
export INSTALLATION_NAMESPACE=default

mirrord exec -f mirrord.json -- poetry run python3 -m robusta.runner.main
#mirrord exec -f mirrord.json -- poetry run memray run -m robusta.runner.main
#poetry run python3 -m robusta.runner.main