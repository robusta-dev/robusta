import hashlib
import importlib.util
import logging
import os
import pkgutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import threading
from inspect import getmembers
from typing import Dict, Optional

import dpath.util
import requests
import toml
import yaml

from robusta.core.model.env_vars import (
    CUSTOM_PLAYBOOKS_ROOT,
    DEFAULT_PLAYBOOKS_PIP_INSTALL,
    DEFAULT_PLAYBOOKS_ROOT,
    INTERNAL_PLAYBOOKS_ROOT,
    PLAYBOOKS_CONFIG_FILE_PATH,
    PLAYBOOKS_ROOT,
)
from robusta.core.model.runner_config import PlaybookRepo, RunnerConfig
from robusta.core.playbooks.actions_registry import Action, ActionsRegistry
from robusta.core.playbooks.playbooks_event_handler import PlaybooksEventHandler
from robusta.integrations.git.git_repo import (
    GIT_HTTPS_PREFIX,
    GIT_SSH_PREFIX,
    LOCAL_PATH_URL_PREFIX,
    GitRepo,
    GitRepoManager,
)
from robusta.integrations.prometheus.models import update_severity_map
from robusta.integrations.receiver import ActionRequestReceiver
from robusta.integrations.scheduled.playbook_scheduler_manager_impl import PlaybooksSchedulerManagerImpl
from robusta.integrations.scheduled.trigger import ScheduledTriggerEvent
from robusta.model.config import PlaybooksRegistry, PlaybooksRegistryImpl, Registry, SinksRegistry
from robusta.model.playbook_definition import PlaybookDefinition
from robusta.utils.cluster_provider_discovery import cluster_provider
from robusta.utils.file_system_watcher import FileSystemWatcher


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
        self.watcher = FileSystemWatcher(self.root_playbook_path, self.reload)
        self.conf_watcher = FileSystemWatcher(self.config_file_path, self.reload)
        self.reload("initialization")

    def close(self):
        self.watcher.stop_watcher()
        self.conf_watcher.stop_watcher()

    def reload(self, description: str):
        self.__reload_playbook_packages(description)
        self.registry.get_event_emitter().emit_event("config_reload")

    def __reload_scheduler(self, playbooks_registry: PlaybooksRegistry):
        scheduler = self.registry.get_scheduler()
        if not scheduler:  # no scheduler yet, initialization
            scheduler = PlaybooksSchedulerManagerImpl(event_handler=self.event_handler)
            self.registry.set_scheduler(scheduler)

        scheduler.update(playbooks_registry.get_playbooks(ScheduledTriggerEvent()))

    def __reload_receiver(self) -> None:
        robusta_sinks = self.registry.get_sinks().get_robusta_sinks()
        if not robusta_sinks:
            logging.info("No robusta sinks found, skipping receiver creation")
            return
        robusta_sink = robusta_sinks[0]

        receiver = self.registry.get_receiver()
        if not receiver:  # no existing receiver, just start one
            self.__create_receiver(robusta_sink)
            return

        updated_account_id = robusta_sink.account_id
        updated_cluster_name = robusta_sink.cluster_name

        if updated_account_id != receiver.account_id or updated_cluster_name != receiver.cluster_name:
            # need to re-create the receiver
            receiver.stop()
            self.__create_receiver(robusta_sink)

    def __create_receiver(self, robusta_sink: "RobustaSink"):
        receiver = ActionRequestReceiver(self.event_handler, robusta_sink)
        self.registry.set_receiver(receiver)
        return receiver

    @staticmethod
    def __get_package_name_from_pyproject(local_path: str) -> str:
        with open(os.path.join(local_path, "pyproject.toml"), "r") as pyproj_toml:
            data = pyproj_toml.read()
            parsed = toml.loads(data)
            return dpath.util.get(parsed, "tool/poetry/name", default="")

    @classmethod
    def __get_package_name(cls, local_path) -> str:
        package_name = ConfigLoader.__get_package_name_from_pyproject(local_path)
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
                if playbooks_repo.pip_install:  # skip playbooks that are already in site-packages
                    # Check that the config specifies an external Python package to be downloaded
                    # and installed in Robusta.
                    url = playbooks_repo.url
                    if url.startswith(("https://", "http://")) and url.endswith((".tar.gz", ".tgz")):
                        if url.startswith("http://"):
                            logging.warning(f"Downloading a playbook package from non-https source f{url}")

                        playbook_package = self.install_package_remote_tgz(
                            url=url, headers=playbooks_repo.http_headers, build_isolation=playbooks_repo.build_isolation
                        )
                    elif url.startswith((GIT_SSH_PREFIX, GIT_HTTPS_PREFIX)):
                        repo = GitRepo(url, playbooks_repo.key.get_secret_value(), playbooks_repo.branch)
                        pkg_path = repo.repo_local_path
                        self.install_package(
                            pkg_path=repo.repo_local_path, build_isolation=playbooks_repo.build_isolation
                        )
                        playbook_package = self.__get_package_name(local_path=pkg_path)
                    elif url.startswith(LOCAL_PATH_URL_PREFIX):
                        pkg_path = url.replace(LOCAL_PATH_URL_PREFIX, "")
                        self.install_package(pkg_path=pkg_path, build_isolation=playbooks_repo.build_isolation)
                        playbook_package = self.__get_package_name(local_path=pkg_path)
                    else:
                        raise Exception(
                            f"Illegal playbook repo url {url}. "
                            f"Must start with '{GIT_SSH_PREFIX}', '{GIT_HTTPS_PREFIX}' or '{LOCAL_PATH_URL_PREFIX}'"
                        )

                playbook_packages.append(playbook_package)
            except Exception:
                logging.error(f"Failed to add playbooks repo {playbook_package}", exc_info=True)

        for package_name in playbook_packages:
            self.__import_playbooks_package(actions_registry, package_name)

    @classmethod
    def install_package(cls, pkg_path: str, build_isolation: bool) -> str:
        logging.debug(f"Installing package {pkg_path}")
        if not os.path.exists(pkg_path):
            # In case the repo url was defined before it was actually loaded. Note we don't
            # perform this check when the pkg is sourced from an externally hosted tgz etc.
            logging.error(f"Playbook local path {pkg_path} does not exist. Skipping")
            raise Exception(f"Playbook local path {pkg_path} does not exist. Skipping")

        # Adding to pip the playbooks repo from local_path
        extra_pip_args = ["--no-build-isolation"] if build_isolation else []

        subprocess.check_call([sys.executable, "-m", "pip", "install"] + extra_pip_args + [pkg_path])

    @classmethod
    def __import_playbooks_package(cls, actions_registry: ActionsRegistry, package_name: str):
        logging.info(f"Importing actions package {package_name}")
        # Reload is required for modules that are already loaded
        pkg = importlib.reload(importlib.import_module(package_name))
        playbooks_modules = [name for _, name, _ in pkgutil.walk_packages(path=pkg.__path__)]
        for playbooks_module in playbooks_modules:
            try:
                module_name = ".".join([package_name, playbooks_module])
                logging.info(f"importing actions from {module_name}")
                # Reload is required for modules that are already loaded
                m = importlib.reload(importlib.import_module(module_name))
                playbook_actions = getmembers(m, Action.is_action)
                for action_name, action_func in playbook_actions:
                    actions_registry.add_action(action_func)
            except Exception:
                logging.error(f"failed to module {playbooks_module}", exc_info=True)

    def __reload_playbook_packages(self, change_name):
        logging.info(f"Reloading playbook packages due to change on {change_name}")
        with self.reload_lock:
            try:
                runner_config = self.__load_runner_config(self.config_file_path)
                if runner_config is None:
                    return
                cluster_provider.init_provider_discovery()
                self.registry.set_global_config(runner_config.global_config)
                self.registry.set_relabel_config(runner_config.alert_relabel)
                update_severity_map(runner_config.global_config)

                action_registry = ActionsRegistry()
                # reordering playbooks repos, so that the internal and default playbooks will be loaded first
                # It allows to override these, with playbooks loaded afterwards
                playbook_repos: Dict[str, PlaybookRepo] = {}
                playbook_repos["robusta.core.playbooks.internal"] = PlaybookRepo(
                    url=INTERNAL_PLAYBOOKS_ROOT, pip_install=False
                )
                # order matters! Loading the default first, allows overriding it if adding package with the same name
                # since python 3.7, iteration order is identical to insertion order, if dict didn't change
                # default playbooks
                playbook_repos[self.__get_package_name(DEFAULT_PLAYBOOKS_ROOT)] = PlaybookRepo(
                    url=f"file://{DEFAULT_PLAYBOOKS_ROOT}", pip_install=DEFAULT_PLAYBOOKS_PIP_INSTALL
                )

                for url, repo in runner_config.playbook_repos.items():
                    playbook_repos[url] = repo

                # saving the ordered playbooks repo into runner config
                runner_config.playbook_repos = playbook_repos
                # custom playbooks
                if os.path.exists(CUSTOM_PLAYBOOKS_ROOT):
                    for custom_playbooks_location in os.listdir(CUSTOM_PLAYBOOKS_ROOT):
                        try:
                            location = os.path.join(CUSTOM_PLAYBOOKS_ROOT, custom_playbooks_location)
                            runner_config.playbook_repos[self.__get_package_name(location)] = PlaybookRepo(
                                url=f"file://{location}"
                            )
                        except Exception:  # This may happen because of the lost+found directory
                            logging.warning(f"Skipping custom actions directory {custom_playbooks_location}")
                else:
                    logging.info(f"No custom playbooks defined at {CUSTOM_PLAYBOOKS_ROOT}")

                self.__load_playbooks_repos(action_registry, runner_config.playbook_repos)

                # This needs to be set before the robusta sink is created since a cluster status is sent on creation
                self.registry.set_light_actions(runner_config.light_actions if runner_config.light_actions else [])

                (sinks_registry, playbooks_registry) = self.__prepare_runtime_config(
                    runner_config,
                    self.registry.get_sinks(),
                    action_registry,
                    self.registry,
                )
                # clear git repos, so it would be re-initialized
                GitRepoManager.clear_git_repos()

                self.__reload_scheduler(playbooks_registry)
                self.registry.set_actions(action_registry)
                self.registry.set_playbooks(playbooks_registry)
                self.registry.set_sinks(sinks_registry)
                self.__reload_receiver()

                telemetry = self.registry.get_telemetry()
                telemetry.playbooks_count = len(runner_config.active_playbooks) if runner_config.active_playbooks else 0
                telemetry.account_id = hashlib.sha256(
                    str(runner_config.global_config.get("account_id", "no_account")).encode("utf-8")
                ).hexdigest()
                telemetry.cluster_id = hashlib.sha256(
                    str(runner_config.global_config.get("cluster_name", "no_cluster")).encode("utf-8")
                ).hexdigest()

            except Exception:
                logging.error(
                    "Error (re)loading playbooks/related resources, exiting.",
                    exc_info=True,
                )
                # Kill the whole process group (which means this process and all of its descendant
                # processes). The rest of the runner shutdown happens in robusta.runner.process_setup.
                os.killpg(os.getpgid(0), signal.SIGTERM)

    @classmethod
    def __prepare_runtime_config(
        cls,
        runner_config: RunnerConfig,
        sinks_registry: SinksRegistry,
        actions_registry: ActionsRegistry,
        registry: Registry,
    ) -> (SinksRegistry, PlaybooksRegistry):
        existing_sinks = sinks_registry.get_all() if sinks_registry else {}
        new_sinks = SinksRegistry.construct_new_sinks(runner_config.sinks_config, existing_sinks, registry)
        sinks_registry = SinksRegistry(new_sinks)

        # TODO we will replace it with a more generic mechanism, as part of the triggers separation task
        # First, we load the internal playbooks, then add the user activated playbooks
        # Order matters. Internal playbooks, should be added first, and run first
        active_playbooks = [
            PlaybookDefinition(
                triggers=[
                    {
                        "on_kubernetes_resource_operation": {
                            "resources": ["deployment", "replicaset", "daemonset", "statefulset", "pod", "job"]
                        }
                    }
                ],
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
            logging.warning(f"config file not found at {config_file_path} - not configuring any playbooks.")
            return None

        logging.info(f"loading config {config_file_path}")
        with open(config_file_path) as file:
            yaml_content = yaml.safe_load(file)
            return RunnerConfig(**yaml_content)

    @classmethod
    def install_package_remote_tgz(cls, url: str, headers, build_isolation: bool) -> Optional[str]:
        with tempfile.NamedTemporaryFile(suffix=".tgz") as f:
            r = requests.get(url, stream=True, headers=headers)
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)

            f.flush()

            with tarfile.open(f.name, "r:gz") as tar, tempfile.TemporaryDirectory() as temp_dir:
                tar.extractall(path=temp_dir)
                extracted_items = os.listdir(temp_dir)

                pkg_path = temp_dir
                if len(extracted_items) == 1:
                    pkg_path = os.path.join(temp_dir, extracted_items[0])

                cls.install_package(pkg_path=pkg_path, build_isolation=build_isolation)
                return cls.__get_package_name(local_path=pkg_path)
