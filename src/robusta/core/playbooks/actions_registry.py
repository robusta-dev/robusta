import inspect
from typing import Callable, Optional, Dict, Type

from pydantic.main import BaseModel

from ..model.events import ExecutionBaseEvent, ExecutionEventBaseParams
from ...utils.decorators import doublewrap


@doublewrap
def action(func: Callable):
    setattr(func, "_action_name", func.__name__)
    return func


class Action:
    def __init__(
        self,
        action_name: str,
        func: Callable,
        event_type: Type[ExecutionBaseEvent],
        params_type: Type[BaseModel] = None,
    ):
        self.action_name = action_name
        self.func = func
        self.event_type = event_type
        self.params_type = params_type
        self.from_params_func = None
        self.from_params_parameter_class = None
        if vars(event_type).get("from_params"):  # execution event has 'from_params'
            self.from_params_func = getattr(event_type, "from_params")
            from_params_signature = inspect.signature(self.from_params_func)
            self.from_params_parameter_class = list(
                from_params_signature.parameters.values()
            )[0].annotation


class ActionsRegistry:
    _actions: Dict[str, Action] = {}

    def add_action(self, action_name: str, func: Callable):
        func_params = iter(inspect.signature(func).parameters.values())

        event_type = next(func_params).annotation
        if not issubclass(event_type, ExecutionBaseEvent):
            raise Exception(
                f"Illegal action first parameter {event_type}. Must extend ExecutionBaseEvent"
            )

        action_params = next(func_params, None)
        if action_params:
            action_params = action_params.annotation
            if not issubclass(action_params, BaseModel):
                raise Exception(
                    f"Illegal action second parameter {action_params}. Action params must extend BaseModel"
                )

        self._actions[action_name] = Action(
            action_name, func, event_type, action_params
        )

    def get_action(self, action_name: str) -> Optional[Action]:
        return self._actions.get(action_name)

    @classmethod
    def is_playbook_action(cls, func) -> bool:
        return (
            inspect.isfunction(func) and getattr(func, "_action_name", None) is not None
        )

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
