import inspect
from typing import Callable, Optional, Dict, Type

from pydantic.main import BaseModel

from ..model.base_params import ActionParams
from ..model.events import ExecutionBaseEvent, ExecutionEventBaseParams
from ...utils.decorators import doublewrap


class NotAnActionException(Exception):
    def __init__(self, obj):
        super(NotAnActionException, self).__init__(f"{obj}  is not a playbook action")


@doublewrap
def action(func: Callable):
    """
    Decorator to mark functions as playbook actions
    """
    setattr(func, "_action_name", func.__name__)
    return func


class Action:
    def __init__(
        self,
        func: Callable,
    ):
        if not self.is_action(func):
            raise NotAnActionException(func)

        self.action_name = func.__name__
        self.func = func
        self.event_type = self.__get_action_event_type(func)
        self.params_type = self.__get_action_params_type(func)
        self.from_params_func = None
        self.from_params_parameter_class = None
        if vars(self.event_type).get(
            "from_params"
        ):  # execution event has 'from_params'
            self.from_params_func = getattr(self.event_type, "from_params")
            from_params_signature = inspect.signature(self.from_params_func)
            self.from_params_parameter_class = list(
                from_params_signature.parameters.values()
            )[0].annotation

    @staticmethod
    def is_action(func):
        return (
            inspect.isfunction(func) and getattr(func, "_action_name", None) is not None
        )

    @staticmethod
    def __get_action_event_type(func: Callable):
        """
        Returns the event_type of a playbook action.
        E.g. given an action like:

            @action
            def some_playbook(event: PodEvent, params: MyPlaybookParams):
                pass

        This function returns the class PodEvent
        """
        func_params = iter(inspect.signature(func).parameters.values())
        event_type = next(func_params).annotation
        if not issubclass(event_type, ExecutionBaseEvent):
            raise Exception(
                f"Illegal action first parameter {event_type}. Must extend ExecutionBaseEvent"
            )
        return event_type

    @staticmethod
    def __get_action_params_type(func: Callable):
        """
        Returns the parameters class for a playbook action or None if the action has no parameters
        E.g. given an action like:

            @action
            def some_playbook(event: PodEvent, params: MyPlaybookParams):
                pass

        This function returns the class MyPlaybookParams
        """
        func_params = iter(inspect.signature(func).parameters.values())
        next(func_params)  # skip the event parameter
        action_params = next(func_params, None)
        if not action_params:
            return None
        params_cls = action_params.annotation
        if not issubclass(params_cls, BaseModel):
            raise Exception(
                f"Illegal action second parameter {params_cls}. Action params must extend BaseModel"
            )
        return params_cls


class ActionsRegistry:
    _actions: Dict[str, Action] = {}

    def add_action(self, func: Callable):
        self._actions[func.__name__] = Action(func)

    def get_action(self, action_name: str) -> Optional[Action]:
        return self._actions.get(action_name)

    def get_external_actions(
        self,
    ) -> [(str, Type[ExecutionEventBaseParams], Optional[Type[BaseModel]])]:
        """Should be used to prepare calling schema for each action"""
        return [
            (
                action_def.action_name,
                action_def.from_params_parameter_class,
                action_def.params_type,
            )
            for action_def in self._actions.values()
            if action_def.from_params_func
        ]
