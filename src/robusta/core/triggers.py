import copy
import logging

from .model.playbook_deploy_config import PlaybookDeployConfig
from ..core.sinks.sink_manager import SinkManager
from .model.trigger_params import TriggerParams
from .model.playbook_hash import playbook_hash

from ..core.active_playbooks import get_active_playbooks, get_playbook_inventory
from ..core.model.runner_config import RunnerConfig
from ..core.schedule.scheduler import Scheduler


def clear_active_playbooks():
    get_active_playbooks().clear()


class DeployCommand:
    def __init__(self, deploy_func, func, trigger_params, sinks, action_params=None):
        self.deploy_func = deploy_func
        self.func = func
        self.trigger_params = trigger_params
        self.sinks = sinks
        self.action_params = action_params
        if (
            action_params is not None
            and getattr(action_params, "pre_deploy_func", None) is not None
        ):
            action_params.pre_deploy_func(trigger_params)
        self.playbook_id = playbook_hash(func, trigger_params, action_params)


def deploy_playbook_config(runner_config: RunnerConfig):
    cluster_name = runner_config.global_config.get("cluster_name", "")
    SinkManager.update_sinks_config(runner_config.sinks_config, cluster_name)

    default_sinks = runner_config.global_config.get("sinks", [])
    if not default_sinks:
        logging.warning(
            f"No default sinks defined. By default, actions results are ignored."
        )

    deploy_commands = []
    # TODO we will replace it with a more generic mechanism, as part of the triggers separation task
    # First, we load the internal playbooks, then add the user activated playbooks
    # Order matters. Internal playbooks, should be added first, and run first
    active_playbooks = [PlaybookDeployConfig(name="cluster_discovery_updates")]
    active_playbooks.extend(runner_config.active_playbooks)
    for playbook_config in active_playbooks:
        playbook_definition = get_playbook_inventory().get(playbook_config.name)
        if playbook_definition is None:
            logging.error(
                f"playbook definition not found. skipping. {playbook_config.name}"
            )  # TODO - should we continue, or not run at all??
            continue

        runtime_trigger_params = copy.deepcopy(
            playbook_definition["default_trigger_params"]
        )
        # first override defaults with global config
        runtime_trigger_params = get_merged_global_config(
            runner_config.global_config, runtime_trigger_params
        )
        # then override the result with trigger_params specific config
        runtime_trigger_params = get_merged_config(
            playbook_config.trigger_params, runtime_trigger_params
        )
        playbooks_sinks = (
            playbook_config.sinks
            if playbook_config.sinks is not None
            else default_sinks
        )
        deploy_func = playbook_definition["deploy_func"]
        if playbook_definition["action_params"] is None:
            deploy_commands.append(
                DeployCommand(
                    deploy_func,
                    playbook_definition["func"],
                    runtime_trigger_params,
                    playbooks_sinks,
                )
            )
        else:
            # in case we have params, we have to apply the global config on it as well
            playbook_config.action_params = merge_global_params(
                runner_config.global_config, playbook_config.action_params
            )
            deploy_commands.append(
                DeployCommand(
                    deploy_func,
                    playbook_definition["func"],
                    runtime_trigger_params,
                    playbooks_sinks,
                    playbook_definition["action_params"](
                        **playbook_config.action_params
                    ),
                )
            )

    new_playbook_ids = set(
        [deploy_command.playbook_id for deploy_command in deploy_commands]
    )
    clear_active_playbooks()

    # unschedule playbooks that doesn't exist any more
    Scheduler.unschedule_deleted_playbooks(new_playbook_ids)

    for deploy_command in deploy_commands:
        if deploy_command.action_params is None:
            deploy_command.deploy_func(
                deploy_command.func, deploy_command.trigger_params, deploy_command.sinks
            )
        else:
            deploy_command.deploy_func(
                deploy_command.func,
                deploy_command.trigger_params,
                deploy_command.sinks,
                deploy_command.action_params,
            )


def merge_global_params(global_config: dict, config_params: dict) -> dict:
    merged = global_config.copy()
    merged.update(config_params)
    return merged


def get_merged_global_config(
    global_config: dict, config_defaults: TriggerParams
) -> TriggerParams:
    config_defaults_fields = config_defaults.__fields_set__
    for attribute in global_config.keys():
        if global_config.get(attribute) is not None and hasattr(
            config_defaults_fields, attribute
        ):
            setattr(config_defaults, attribute, getattr(global_config, attribute))
    return config_defaults


def get_merged_config(
    config_overrides: TriggerParams, config_defaults: TriggerParams
) -> TriggerParams:
    for attribute in config_overrides.__fields_set__:
        if getattr(config_overrides, attribute) is not None:
            setattr(config_defaults, attribute, getattr(config_overrides, attribute))
    return config_defaults
