import glob
import importlib.util
import logging
import os
import subprocess
import sys

import yaml

from ..integrations.git.git_repo import GitRepoManager
from ..core.active_playbooks import clear_playbook_inventory
from ..core.triggers import deploy_playbook_config, RunnerConfig
from ..utils.directory_watcher import DirWatcher


class ConfigHandler:
    def __init__(self):
        custom_playbooks_root = os.environ.get("CUSTOM_PLAYBOOKS_ROOT")
        # we add this to sys.path so that playbooks can import from one another with:
        # from other_playbook import shared_function
        sys.path.append(custom_playbooks_root)
        reload_runner_configuration(custom_playbooks_root)
        self.watcher = DirWatcher(custom_playbooks_root, reload_runner_configuration)

    def close(self):
        self.watcher.stop_watcher()


def reload_runner_configuration(custom_playbooks_root):
    try:
        logging.info(f"reloading custom playbooks from {custom_playbooks_root}")
        if not os.path.exists(custom_playbooks_root):
            logging.error(f"playbooks configuration not found {custom_playbooks_root}")
            return
        reload_scripts(custom_playbooks_root)
        reload_deploy_config(custom_playbooks_root)
    except Exception as e:
        logging.exception(
            f"unknown error reloading playbooks. will try again when they next change. exception={e}"
        )


def reload_scripts(path):
    install_requirements(os.path.join(path, "requirements.txt"))

    python_files = glob.glob(f"{path}/*.py")
    clear_playbook_inventory()

    if len(python_files) == 0:
        logging.warning("no playbook scripts to load")
        return

    for script in python_files:
        try:
            logging.info(f"loading playbooks from file {script}")
            filename = os.path.basename(script)
            (module_name, ext) = os.path.splitext(filename)
            spec = importlib.util.spec_from_file_location(module_name, script)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as e:
            logging.error(f"error loading playbooks from file {script}. exception={e}")

    logging.info(f"{len(python_files)} custom playbooks loaded")


def reload_deploy_config(path):
    # TODO: there is a race condition here where we can lose events if they arrive while we are reloading
    # even if the script that should handle those events was active in both versions
    active_playbooks_file_name = os.path.join(path, "active_playbooks.yaml")
    if not os.path.exists(active_playbooks_file_name):
        logging.warning(
            f"no playbook definition file found at {active_playbooks_file_name}. not configuring any playbooks."
        )
        return

    logging.info(f"loading active playbooks config {active_playbooks_file_name}")
    with open(active_playbooks_file_name) as file:
        yaml_content = yaml.safe_load(file)
        runner_config = RunnerConfig(**yaml_content)

    deploy_playbook_config(runner_config)

    # clear git repos, so it would be re-initialized
    GitRepoManager.clear_git_repos()


def install_requirements(requirements_file_name):
    if os.path.exists(requirements_file_name):
        logging.info(f"installing custom requirements file {requirements_file_name}")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", requirements_file_name]
        )
        logging.info("custom requirements installed")
    else:
        logging.warning(f"requirements file {requirements_file_name} not found")
