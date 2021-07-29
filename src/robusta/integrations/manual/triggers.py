import logging
from functools import wraps
from dataclasses import dataclass, field
import pydantic
from typing import List

from ..base_handler import handle_event
from ...core.active_playbooks import activate_playbook, register_playbook
from ...core.model.playbook_hash import playbook_hash
from ...utils.decorators import doublewrap
from ...core.model.trigger_params import TriggerParams
from ...core.model.cloud_event import CloudEvent
from ...core.model.events import EventType, BaseEvent


@dataclass
class ManualTriggerEvent(BaseEvent):
    trigger_name: str = ""
    data: dict = field(default_factory=dict)


@doublewrap
def on_manual_trigger(func):
    return register_playbook(
        func, deploy_manual_trigger, TriggerParams(trigger_name=func.__name__)
    )


def deploy_manual_trigger(
    func, trigger_params: TriggerParams, named_sinks: List[str], action_params=None
):
    @wraps(func)
    def wrapper(cloud_event: CloudEvent):
        trigger_event = ManualTriggerEvent(
            trigger_name=cloud_event.subject, data=cloud_event.data
        )
        logging.debug(
            f"checking if we should run manually triggered playbook {func}. trigger_name in request is {trigger_event.trigger_name} and playbook trigger_name is {trigger_params.trigger_name}"
        )

        if trigger_event.trigger_name != trigger_params.trigger_name:
            logging.debug("not running")
            return

        try:
            return handle_event(
                func, trigger_event, action_params, "manual", named_sinks
            )
        except pydantic.error_wrappers.ValidationError as e:
            logging.error(f"{e}")

    playbook_id = playbook_hash(func, trigger_params, action_params)
    activate_playbook(EventType.MANUAL_TRIGGER, wrapper, func, playbook_id)
    return wrapper
