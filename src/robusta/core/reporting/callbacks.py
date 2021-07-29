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


class PlaybookCallbackRequest(BaseModel):
    func_name: str
    func_file: str
    func_hash: str
    context: str

    @classmethod
    def create_for_func(cls, func: Callable, context: Any, text: str):
        if func is None:
            raise Exception(
                f"The callback for choice {text} is None. Did you accidentally pass `foo()` as a callback and not `foo`?"
            )
        if not callback_registry.is_callback_in_registry(func):
            raise Exception(
                f"{func} is not a function that was decorated with @on_report_callback or it somehow"
                f" has the wrong version (e.g. multiple functions with the same name were decorated "
                f"with @on_report_callback)"
            )

        return cls(
            func_name=func.__name__,
            func_file=inspect.getsourcefile(func),
            func_hash=get_function_hash(func),
            context=context,
        )


class CallbackRegistry:
    def __init__(self):
        self.callbacks = {}

    def register_callback(self, func: Callable):
        key = self._get_callback_key_for_func(func)
        logging.info(f"inserting callback with key={key}")
        if key in self.callbacks:
            logging.warning(
                f"overriding existing callback in registry; new func={func}"
            )
        self.callbacks[key] = func

    def is_callback_in_registry(self, func: Callable):
        key = self._get_callback_key_for_func(func)
        return key in self.callbacks

    def lookup_callback(self, callback_request: PlaybookCallbackRequest):
        logging.debug(
            f"looking up callback with func_name={callback_request.func_name} and func_file={callback_request.func_file}"
        )
        key = (callback_request.func_name, callback_request.func_file)
        if key not in self.callbacks:
            return None

        func = self.callbacks[key]
        if callback_request.func_hash != get_function_hash(func):
            logging.warning(
                "callback hash doesn't match! calling a different version of the function than the original one!"
            )
        return func

    @staticmethod
    def _get_callback_key_for_func(func: Callable):
        return func.__name__, inspect.getsourcefile(func)


@dataclass
class SinkCallbackEvent(BaseEvent):
    source_channel_name: str = ""
    source_channel_id: str = ""
    source_user_id: str = ""
    source_context: str = ""
    source_message: str = ""


callback_registry = CallbackRegistry()


@doublewrap
def on_sink_callback(func):
    callback_registry.register_callback(func)
    return func
