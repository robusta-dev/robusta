import inspect
import logging
from typing import Callable
from collections import defaultdict
from sys import exc_info

import better_exceptions  # type: ignore
from ..core.model.cloud_event import CloudEvent


class PlaybookWrapper:
    def __init__(self, wrapper, playbook_id):
        self.wrapper = wrapper
        self.playbook_id = playbook_id


active_playbooks = defaultdict(list)  # maps trigger types to active playbooks
playbook_inventory = {}


def get_playbook_inventory():
    return playbook_inventory


def get_active_playbooks():
    return active_playbooks


def get_function_params_class(func: Callable):
    """Inspects a playbook function's signature and returns the type of the param class if it exists"""
    func_signature = inspect.signature(func)
    if len(func_signature.parameters) == 1:
        return None
    parameter_name = list(func_signature.parameters)[1]
    return func_signature.parameters[parameter_name].annotation


def register_playbook(func, deploy_func, default_trigger_params):
    get_playbook_inventory()[func.__name__] = {
        "func": func,
        "default_trigger_params": default_trigger_params,
        "deploy_func": deploy_func,
        "action_params": get_function_params_class(func),
    }
    func.__playbook = playbook_inventory[func.__name__]


def clear_playbook_inventory():
    playbook_inventory.clear()


def activate_playbook(trigger_type, wrapper, func, playbook_id):
    logging.info(f"adding handler {func} playbook_id {playbook_id}")
    active_playbooks[trigger_type.name].append(PlaybookWrapper(wrapper, playbook_id))


def run_playbooks(cloud_event: CloudEvent):
    # TODO: Ideally we would do the conversion to a concrete event class here so that we pass the same event
    # object to all playbooks that are triggered and they can each add stuff to the reporting blocks
    description = cloud_event.data["description"].replace("\n", "")
    logging.debug(f"received cloud event: {description}")
    handlers = active_playbooks[cloud_event.type]
    logging.debug(f"relevant handlers: {handlers}")
    for playbook_wrapper in handlers:
        try:
            playbook_wrapper.wrapper(cloud_event)
        except Exception as e:
            _, _, traceback = exc_info()
            msg = "\n".join(
                better_exceptions.format_exception(e.__class__, e, traceback)
            )
            logging.exception(f"got exception running handler: {msg}")
