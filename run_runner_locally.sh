#!/bin/bash
set -e

export PYTHON_BINARY=python3.9
export RED='\033[0;31m'
export NC='\033[0m' # No Color


# Check if Python 3.9 or higher is installed
if ! $PYTHON_BINARY -c "import sys; exit(not (sys.version_info.major == 3 and sys.version_info.minor >= 9))"; then
  echo -e "${RED}Error: Python 3.9 or higher is not installed or was not run\n${NC}"
  echo "You are using `$PYTHON_BINARY --version` located at `which $PYTHON_BINARY`"
  echo "To change your Python version, edit the PYTHON_BINARY variable at the top of this script"
  exit 1
fi

#if ! $PYTHON_BINARY -c "import poetry" &> /dev/null; then
#  echo -e "Error: Poetry is not installed for the Python binary you chose.\n"
#  echo "You are using `$PYTHON_BINARY --version` located at `which $PYTHON_BINARY`"
#  echo "To change your Python version, edit the PYTHON_BINARY variable at the top of this script"
#  exit 1
#fi

# Check if Poetry is installed globally
if ! command -v poetry &> /dev/null
then
    echo -e "${RED}Poetry is not installed globally. Make sure the `poetry` command works${NC}"
    exit 1
fi

echo "Python 3.9+ and Poetry are installed."
echo "Now setting up Robusta"

poetry env use $PYTHON_BINARY
poetry install --extras=all
echo "All dependencies installed"


echo "Setting up local runner environment"
mkdir -p deployment/playbooks/defaults
ln -fsw $(pwd)/playbooks/robusta_playbooks/ ./deployment/playbooks/defaults
ln -fsw $(pwd)/playbooks/pyproject.toml ./deployment/playbooks/defaults

echo "Checking if runner can listen on port 5000"
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${RED}Error: Port 5000 is already in use. Exiting.${NC}"
    exit 1
fi

echo "Checking for active_playbooks.yaml"
# warning: this doesn't actually run independent of the cluster - e.g. scheduler dal uses cluster state
if [ ! -f "$PWD/deployment/playbooks/active_playbooks.yaml" ]; then
  echo -e "${RED}Error: You need an active_playbooks.yaml to run Robusta locally!${NC}"
  echo "This file must be located at ./deployment/playbooks/active_playboks.yaml"
  echo "You can fix by extracting this file from an existing cluster with Robusta. Run:"
  echo -e "\tkubectl get secret robusta-playbooks-config-secret -o jsonpath='{.data.active_playbooks\.yaml}'  | base64 --decode > ./deployment/playbooks/active_playbooks.yaml"
  echo -e "${RED}After extracting active_playbooks.yaml from your cluster, you MUST change global_config.cluster_name in it!!!!!${NC}"
  exit 1
fi

echo "Installing builtin playbooks"
poetry run python3 -m pip install -e ./deployment/playbooks/defaults

export PLAYBOOKS_CONFIG_FILE_PATH=./deployment/playbooks/active_playbooks.yaml
export INTERNAL_PLAYBOOKS_ROOT=./src/robusta/core/playbooks/internal
export PLAYBOOKS_ROOT=./deployment/playbooks
export PORT=5000
export REPO_LOCAL_BASE_DIR=./deployment/git_playbooks
export INSTALLATION_NAMESPACE=default
export TRACE_INCOMING_REQUESTS=true
export LOG_LEVEL=DEBUG

poetry run python3 -m robusta.runner.main

