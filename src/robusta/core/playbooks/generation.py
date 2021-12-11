import yaml
import logging
import jsonref
from collections import defaultdict
from typing import Type, List, Callable, Union, get_origin, get_args
from ..playbooks.base_trigger import BaseTrigger, ExecutionBaseEvent
from ..playbooks.actions_registry import Action
from ..playbooks.trigger import Trigger
from ...utils.json_schema import example_from_schema

# see https://stackoverflow.com/questions/13518819/avoid-references-in-pyyaml
class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


class ExamplesGenerator:
    def __init__(self):
        self.events_to_triggers = defaultdict(set)
        self.triggers_to_yaml = {}

        for field_name, field in Trigger.__fields__.items():
            trigger_classes = [
                t
                for t in self.__get_possible_types(field.type_)
                if issubclass(t, BaseTrigger)
            ]
            if len(trigger_classes) == 0:
                continue

            for t in trigger_classes:
                self.triggers_to_yaml[t] = field_name
                execution_event = t.get_execution_event_type()
                possible_events = [execution_event] + list(
                    cls
                    for cls in execution_event.__mro__
                    if issubclass(cls, ExecutionBaseEvent)
                )
                for e in possible_events:
                    self.events_to_triggers[e].add(t)

    @staticmethod
    def __get_possible_types(t):
        """
        Given a type or a Union of types, returns a list of the actual types
        """
        if get_origin(t) == Union:
            return get_args(t)
        else:
            return [t]

    def get_possible_triggers(self, event_cls: Type[ExecutionBaseEvent]) -> List[str]:
        name = event_cls.__name__
        if name == "ExecutionBaseEvent":
            return ["on_pod_create"]
        triggers = self.events_to_triggers.get(event_cls)
        if triggers is None:
            raise Exception(f"Don't know how to generate an example trigger for {name}")
        return [self.triggers_to_yaml[t] for t in triggers]

    def get_highest_possible_trigger(self, event_cls: Type[ExecutionBaseEvent]) -> str:
        all_triggers = self.get_possible_triggers(event_cls)
        if len(all_triggers) == 1:
            return all_triggers[0]
        elif "on_kubernetes_any_resource_update" in all_triggers:
            return "on_kubernetes_any_resource_update"
        else:
            logging.error(f"picking a random trigger from input: {all_triggers}")
            return all_triggers[0]

    def generate_example_config(self, action_func: Callable):
        action_metadata = Action(action_func)
        trigger = self.get_highest_possible_trigger(action_metadata.event_type)
        example = {
            "actions": [{action_metadata.action_name: {}}],
            "triggers": [{trigger: {}}],
        }
        if action_metadata.params_type:
            action_model = action_metadata.params_type
            # instead of loading the schema as python object directly with action_model.schema()
            # we dump to json and then read-back from json to python using jsonref
            # this is necessary to fix parts of the schema that refer to one another
            # without it we need to understand json references and handle them ourselves
            action_schema = jsonref.loads(action_model.schema_json())
            action_example = example_from_schema(action_schema)
            example["actions"][0][action_metadata.action_name] = action_example
        return yaml.dump(example, Dumper=NoAliasDumper)
