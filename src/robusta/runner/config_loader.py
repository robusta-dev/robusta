import glob
import importlib.util
import logging
import os
import subprocess
import sys
from typing import Optional

import yaml

from ..core.model.env_vars import INTERNAL_PLAYBOOKS_ROOT
from ..integrations.git.git_repo import GitRepoManager
from ..core.active_playbooks import clear_playbook_inventory
from ..core.triggers import deploy_playbook_config, RunnerConfig
from ..utils.directory_watcher import DirWatcher


class ConfigLoader:

    # the structure on disk is:
    # root_playbook_path/
    # |- playbook_dir1
    #    |--- playbook1.py
    #    |--- playbook2.py
    #    |--- requirements.txt
    # |- playbook_dir2
    #    |--- ...
    def __init__(self, config_path: str, root_playbook_path: str):
        self.config_path = config_path
        self.root_playbook_path = root_playbook_path
        self.watcher = DirWatcher(self.root_playbook_path, self.__reload())
        self.__reload()

    def close(self):
        self.watcher.stop_watcher()

    def __reload(self):
        try:
            # TODO: there is a race condition here where we can lose events if they arrive while we are reloading
            # even if the playbook that should handle those events was active in both versions
            # We should ultimately fix this by replacing clear_playbook_inventory() with an atomic call to
            # set_playbook_inventory(playbooks) - but to do so we first have to change the way playbook registration
            # works. In the new design, playbooks should be found instead of registering themselves.
            runner_config = self.__load_config(self.config_path)
            if runner_config is None:
                return

            playbook_directories = [
                os.path.join(self.root_playbook_path, path)
                for path in runner_config.playbook_sets
            ]

            clear_playbook_inventory()
            self.__load_playbook_directory(INTERNAL_PLAYBOOKS_ROOT)
            for playbook_dir in playbook_directories:
                self.__load_playbook_directory(playbook_dir)

            deploy_playbook_config(runner_config)
            # clear git repos, so it would be re-initialized
            GitRepoManager.clear_git_repos()

        except Exception as e:
            logging.exception(
                f"unknown error reloading playbooks. will try again when they next change. exception={e}"
            )

    @classmethod
    def __load_config(cls, config_path) -> Optional[RunnerConfig]:
        if not os.path.exists(config_path):
            logging.warning(
                f"config file not found at {config_path} - not configuring any playbooks."
            )
            return None

        logging.info(f"loading config {config_path}")
        with open(config_path) as file:
            yaml_content = yaml.safe_load(file)
            return RunnerConfig(**yaml_content)

    @classmethod
    def __load_playbook_directory(cls, playbook_dir):
        if not os.path.exists(playbook_dir):
            logging.error(f"playbooks directory not found: {playbook_dir}")
            return

        # we add playbook directories to sys.path so that playbooks can do relative imports from one another.
        # e.g. `from other_playbook_file import shared_function`
        if playbook_dir not in sys.path:
            sys.path.append(playbook_dir)

        cls.__install_requirements(os.path.join(playbook_dir, "requirements.txt"))
        python_files = glob.glob(f"{playbook_dir}/*.py")
        if len(python_files) == 0:
            logging.warning(f"no playbook scripts to load in directory {playbook_dir}")
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
                logging.error(
                    f"error loading playbooks from file {script}. exception={e}"
                )

        logging.info(f"{len(python_files)} playbooks loaded from {playbook_dir}")

    @classmethod
    def __install_requirements(cls, requirements_path):
        if os.path.exists(requirements_path):
            logging.info(f"installing requirements file {requirements_path}")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-r", requirements_path]
            )
            logging.info("requirements installed")
        else:
            logging.info(
                f"not installing requirements as file {requirements_path} doesn't exist"
            )
