import glob
import importlib.util
import logging
import os
import subprocess
import sys
import threading
import yaml
from typing import Optional
from inspect import getmembers

from robusta.integrations.receiver import ActionRequestReceiver

from ..integrations.scheduled.trigger import ScheduledTriggerEvent
from ..core.playbooks.playbooks_event_handler import PlaybooksEventHandler
from ..core.model.runner_config import RunnerConfig
from ..core.playbooks.actions_registry import ActionsRegistry, Action
from ..core.model.env_vars import (
    INTERNAL_PLAYBOOKS_ROOT,
    PLAYBOOKS_CONFIG_FILE_PATH,
    PLAYBOOKS_ROOT,
)
from ..integrations.git.git_repo import GitRepoManager
from ..utils.file_system_watcher import FileSystemWatcher
from ..model.playbook_definition import PlaybookDefinition
from ..model.config import (
    Registry,
    SinksRegistry,
    PlaybooksRegistryImpl,
    PlaybooksRegistry,
)
from ..integrations.scheduled.playbook_scheduler_manager_impl import (
    PlaybooksSchedulerManagerImpl,
)


class ConfigLoader:

    # the structure on disk is:
    # root_playbook_path/
    # |- playbook_dir1
    #    |--- playbook1.py
    #    |--- playbook2.py
    #    |--- requirements.txt
    # |- playbook_dir2
    #    |--- ...
    def __init__(
        self,
        registry: Registry,
        event_handler: PlaybooksEventHandler,
    ):
        self.config_file_path = PLAYBOOKS_CONFIG_FILE_PATH
        self.registry = registry
        self.event_handler = event_handler
        self.root_playbook_path = PLAYBOOKS_ROOT
        self.reload_lock = threading.RLock()
        self.watcher = FileSystemWatcher(
            self.root_playbook_path, self.__reload_playbook_packages
        )
        self.conf_watcher = FileSystemWatcher(
            self.config_file_path, self.__reload_playbook_packages
        )
        self.__reload_playbook_packages("initialization")

    def close(self):
        self.watcher.stop_watcher()
        self.conf_watcher.stop_watcher()

    def __reload_scheduler(self, playbooks_registry: PlaybooksRegistry):
        scheduler = self.registry.get_scheduler()
        if not scheduler:  # no scheduler yet, initialization
            scheduler = PlaybooksSchedulerManagerImpl(event_handler=self.event_handler)
            self.registry.set_scheduler(scheduler)

        scheduler.update(playbooks_registry.get_playbooks(ScheduledTriggerEvent()))

    def __reload_receiver(self):
        receiver = self.registry.get_receiver()
        if not receiver:  # no existing receiver, just start one
            self.registry.set_receiver(ActionRequestReceiver(self.event_handler))
            return

        current_account_id = self.event_handler.get_global_config().get("account_id")
        current_cluster_name = self.event_handler.get_global_config().get(
            "cluster_name"
        )

        if (
            current_account_id != receiver.account_id
            or current_cluster_name != receiver.cluster_name
        ):
            # need to re-create the receiver
            receiver.stop()
            self.registry.set_receiver(ActionRequestReceiver(self.event_handler))

    def __reload_playbook_packages(self, change_name):
        logging.info(f"Reloading playbook packages due to change on {change_name}")
        with self.reload_lock:
            try:
                runner_config = self.__load_runner_config(self.config_file_path)
                if runner_config is None:
                    return

                playbook_directories = [
                    os.path.join(self.root_playbook_path, path)
                    for path in runner_config.playbook_sets
                ]

                action_registry = ActionsRegistry()
                self.__load_playbook_directory(INTERNAL_PLAYBOOKS_ROOT, action_registry)
                for playbook_dir in playbook_directories:
                    self.__load_playbook_directory(playbook_dir, action_registry)

                (sinks_registry, playbooks_registry) = self.__prepare_runtime_config(
                    runner_config, self.registry.get_sinks(), action_registry
                )
                # clear git repos, so it would be re-initialized
                GitRepoManager.clear_git_repos()

                self.__reload_scheduler(playbooks_registry)

                self.registry.set_actions(action_registry)
                self.registry.set_playbooks(playbooks_registry)
                self.registry.set_sinks(sinks_registry)

                self.__reload_receiver()
            except Exception as e:
                logging.exception(
                    f"unknown error reloading playbooks. will try again when they next change. exception={e}"
                )

    @classmethod
    def __prepare_runtime_config(
        cls,
        runner_config: RunnerConfig,
        sinks_registry: SinksRegistry,
        actions_registry: ActionsRegistry,
    ) -> (SinksRegistry, PlaybooksRegistry):
        existing_sinks = sinks_registry.get_all() if sinks_registry else {}
        new_sinks = SinksRegistry.construct_new_sinks(
            runner_config.sinks_config, existing_sinks, runner_config.global_config
        )
        sinks_registry = SinksRegistry(new_sinks)

        # TODO we will replace it with a more generic mechanism, as part of the triggers separation task
        # First, we load the internal playbooks, then add the user activated playbooks
        # Order matters. Internal playbooks, should be added first, and run first
        active_playbooks = [
            PlaybookDefinition(
                triggers=[{"on_kubernetes_any_resource_all_changes": {}}],
                actions=[{"cluster_discovery_updates": {}}],
            )
        ]
        active_playbooks.extend(runner_config.active_playbooks)

        playbooks_registry = PlaybooksRegistryImpl(
            active_playbooks,
            actions_registry,
            runner_config.global_config,
            sinks_registry.default_sinks,
        )

        return sinks_registry, playbooks_registry

    @classmethod
    def __load_runner_config(cls, config_file_path) -> Optional[RunnerConfig]:
        if not os.path.exists(config_file_path):
            logging.warning(
                f"config file not found at {config_file_path} - not configuring any playbooks."
            )
            return None

        logging.info(f"loading config {config_file_path}")
        with open(config_file_path) as file:
            yaml_content = yaml.safe_load(file)
            return RunnerConfig(**yaml_content)

    def __load_playbook_directory(
        self, playbook_dir: str, action_registry: ActionsRegistry
    ):
        logging.info(f"Loading playbooks sources from {playbook_dir}")
        if not os.path.exists(playbook_dir):
            logging.error(f"playbooks directory not found: {playbook_dir}")
            return

        # we add playbook directories to sys.path so that playbooks can do relative imports from one another.
        # e.g. `from other_playbook_file import shared_function`
        if playbook_dir not in sys.path:
            sys.path.append(playbook_dir)

        self.__install_requirements(os.path.join(playbook_dir, "requirements.txt"))
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
                playbook_actions = getmembers(module, Action.is_action)
                for (action_name, action_func) in playbook_actions:
                    action_registry.add_action(action_func)
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
