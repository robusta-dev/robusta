# This file contains internal wiring for report callbacks
# Playbook writers don't need to be familiar with this - they should use the API in callbacks.py and not worry about details
import inspect
import logging
from dataclasses import dataclass
from typing import Callable, Any

from pydantic import BaseModel

from ..model.events import BaseEvent
from ...utils.function_hashes import get_function_hash
from ...utils.decorators import doublewrap

class PlaybookCallbackRequest (BaseModel):
    func_name: str
    func_file: str
    func_hash: str
    context: str

    @classmethod
    def create_for_func(cls, func: Callable, context: Any):
        return cls(func_name=func.__name__, func_file=inspect.getsourcefile(func), func_hash=get_function_hash(func), context=context)


class CallbackRegistry:

    def __init__(self):
        self.callbacks = {}

    def register_callback(self, func: Callable):
        key = self._get_callback_key_for_func(func)
        if key in self.callbacks:
            logging.warning(f"overriding existing callback in registry; func={func}")
        self.callbacks[key] = func

    def is_callback_in_registry(self, func: Callable):
        key = self._get_callback_key_for_func(func)
        return key in self.callbacks and self.callbacks[key] == func

    def lookup_callback(self, callback_request: PlaybookCallbackRequest):
        key = (callback_request.func_name, callback_request.func_file)
        if key not in self.callbacks:
            return None

        func = self.callbacks[key]
        if callback_request.func_hash != get_function_hash(func):
            logging.warning("callback hash doesn't match! calling a different version of the function than the original one!")
        return func

    @staticmethod
    def _get_callback_key_for_func(func: Callable):
        return func.__name__, inspect.getsourcefile(func)


# TODO: make this something more generic which isn't slack specific
@dataclass
class ReportCallbackEvent(BaseEvent):
    source_channel_name: str = ""
    source_channel_id: str = ""
    source_user_id: str = ""
    source_context: str = ""
    source_message: str = ""


callback_registry = CallbackRegistry()


@doublewrap
def on_report_callback(func):
    callback_registry.register_callback(func)
    return func
