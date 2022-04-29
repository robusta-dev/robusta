import importlib.util
import logging
import os
import pkgutil
import subprocess
import sys
import threading
import yaml
from typing import Optional, List, Dict
from inspect import getmembers

from ..cli.utils import get_package_name
from ..integrations.receiver import ActionRequestReceiver
from ..integrations.scheduled.trigger import ScheduledTriggerEvent
from ..core.playbooks.playbooks_event_handler import PlaybooksEventHandler
from ..core.model.runner_config import RunnerConfig, PlaybookRepo
from ..core.playbooks.actions_registry import ActionsRegistry, Action
from ..core.model.env_vars import (
    INTERNAL_PLAYBOOKS_ROOT,
    PLAYBOOKS_CONFIG_FILE_PATH,
    PLAYBOOKS_ROOT, DEFAULT_PLAYBOOKS_ROOT, CUSTOM_PLAYBOOKS_ROOT,
)
from ..integrations.git.git_repo import (
    GitRepoManager,
    GitRepo,
    GIT_SSH_PREFIX,
    GIT_HTTPS_PREFIX,
    LOCAL_PATH_URL_PREFIX,
)
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
import hashlib

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

    def reload(self, description: str):
        self.__reload_playbook_packages(description)

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

    @classmethod
    def __get_package_name(cls, local_path) -> str:
        package_name = get_package_name(local_path)
        if not package_name:
            raise Exception(f"Illegal playbooks package {local_path}. Package name not found")
        return package_name

    def __load_playbooks_repos(
        self,
        actions_registry: ActionsRegistry,
        playbooks_repos: Dict[str, PlaybookRepo],
    ):
        playbook_packages = []
        for playbook_package, playbooks_repo in playbooks_repos.items():
            try:
                if (
                    playbooks_repo.pip_install
                ):  # skip playbooks that are already in site-packages
                    if playbooks_repo.url.startswith(GIT_SSH_PREFIX) or playbooks_repo.url.startswith(GIT_HTTPS_PREFIX):
                        repo = GitRepo(
                            playbooks_repo.url,
                            playbooks_repo.key.get_secret_value(),
                        )
                        local_path = repo.repo_local_path
                    elif playbooks_repo.url.startswith(LOCAL_PATH_URL_PREFIX):
                        local_path = playbooks_repo.url.replace(
                            LOCAL_PATH_URL_PREFIX, ""
                        )
                    else:
                        raise Exception(
                            f"Illegal playbook repo url {playbooks_repo.url}. "
                            f"Must start with '{GIT_SSH_PREFIX}', '{GIT_HTTPS_PREFIX}' or '{LOCAL_PATH_URL_PREFIX}'"
                        )

                    if not os.path.exists(
                        local_path
                    ):  # in case the repo url was defined before it was actually loaded
                        logging.error(
                            f"Playbooks local path {local_path} does not exist. Skipping"
                        )
                        continue

                    # Adding to pip the playbooks repo from local_path
                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install", local_path]
                    )
                    playbook_package = self.__get_package_name(local_path=local_path)

                playbook_packages.append(playbook_package)
            except Exception as e:
                logging.error(f"Failed to add playbooks repo {playbook_package}", exc_info=True)

        for package_name in playbook_packages:
            self.__import_playbooks_package(actions_registry, package_name)

    @classmethod
    def __import_playbooks_package(
        cls, actions_registry: ActionsRegistry, package_name: str
    ):
        logging.info(f"Importing actions package {package_name}")
        pkg = importlib.import_module(package_name)
        playbooks_modules = [
            name for _, name, _ in pkgutil.walk_packages(path=pkg.__path__)
        ]
        for playbooks_module in playbooks_modules:
            try:
                module_name = ".".join([package_name, playbooks_module])
                logging.info(f"importing actions from {module_name}")
                m = importlib.import_module(module_name)
                playbook_actions = getmembers(m, Action.is_action)
                for (action_name, action_func) in playbook_actions:
                    actions_registry.add_action(action_func)
            except Exception as e:
                logging.error(f"failed to module {playbooks_module}", exc_info=True)

    def __reload_playbook_packages(self, change_name):
        logging.info(f"Reloading playbook packages due to change on {change_name}")
        with self.reload_lock:
            try:
                runner_config = self.__load_runner_config(self.config_file_path)
                if runner_config is None:
                    return

                self.registry.set_global_config(runner_config.global_config)
                action_registry = ActionsRegistry()
                # reordering playbooks repos, so that the internal and default playbooks will be loaded first
                # It allows to override these, with playbooks loaded afterwards
                playbook_repos: Dict[str, PlaybookRepo] = {}
                playbook_repos[
                    "robusta.core.playbooks.internal"
                ] = PlaybookRepo(url=INTERNAL_PLAYBOOKS_ROOT, pip_install=False)
                # order matters! Loading the default first, allows overriding it if adding package with the same name
                # since python 3.7, iteration order is identical to insertion order, if dict didn't change
                # default playbooks
                playbook_repos[
                    self.__get_package_name(DEFAULT_PLAYBOOKS_ROOT)
                ] = PlaybookRepo(url=f"file://{DEFAULT_PLAYBOOKS_ROOT}")

                for url, repo in runner_config.playbook_repos.items():
                    playbook_repos[url] = repo

                # saving the ordered playbooks repo into runner config
                runner_config.playbook_repos = playbook_repos
                # custom playbooks
                if os.path.exists(CUSTOM_PLAYBOOKS_ROOT):
                    for custom_playbooks_location in os.listdir(CUSTOM_PLAYBOOKS_ROOT):
                        location = os.path.join(CUSTOM_PLAYBOOKS_ROOT, custom_playbooks_location)
                        runner_config.playbook_repos[
                            self.__get_package_name(location)
                        ] = PlaybookRepo(url=f"file://{location}")
                else:
                    logging.info(f"No custom playbooks defined at {CUSTOM_PLAYBOOKS_ROOT}")

                self.__load_playbooks_repos(
                    action_registry, runner_config.playbook_repos
                )

                (sinks_registry, playbooks_registry) = self.__prepare_runtime_config(
                    runner_config, self.registry.get_sinks(), action_registry, self.registry
                )
                # clear git repos, so it would be re-initialized
                GitRepoManager.clear_git_repos()

                self.__reload_scheduler(playbooks_registry)

                self.registry.set_actions(action_registry)
                self.registry.set_playbooks(playbooks_registry)
                self.registry.set_sinks(sinks_registry)

                telemetry = self.registry.get_telemetry()
                telemetry.playbooks_count = len(runner_config.active_playbooks) if runner_config.active_playbooks else 0
                telemetry.account_id = hashlib.sha256(str(runner_config.global_config.get("account_id", "no_account")).encode("utf-8")).hexdigest()
                telemetry.cluster_id = hashlib.sha256(str(runner_config.global_config.get("cluster_name", "no_cluster")).encode("utf-8")).hexdigest()

                self.__reload_receiver()
            except Exception as e:
                logging.error(f"unknown error reloading playbooks. will try again when they next change", exc_info=True)

    @classmethod
    def __prepare_runtime_config(
        cls,
        runner_config: RunnerConfig,
        sinks_registry: SinksRegistry,
        actions_registry: ActionsRegistry,
        registry : Registry
    ) -> (SinksRegistry, PlaybooksRegistry):
        existing_sinks = sinks_registry.get_all() if sinks_registry else {}
        new_sinks = SinksRegistry.construct_new_sinks(
            runner_config.sinks_config, existing_sinks, registry
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
        if runner_config.active_playbooks:
            active_playbooks.extend(runner_config.active_playbooks)
        else:
            logging.warning("No active playbooks configured")

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
