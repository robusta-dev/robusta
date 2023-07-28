import argparse
import glob
import importlib
import inspect
import os
from typing import Callable

from pydantic import BaseModel
from robusta.api import Action

from robusta.core.playbooks.generation import ExamplesGenerator

# creating this is slightly expensive so we create one global instance and re-use it
generator = ExamplesGenerator()
triggers = dict((v, k) for k, v in generator.triggers_to_yaml.items())
print(triggers)

class PlaybookDescription(BaseModel):
    function_name: str
    docs: str = None
    src: str
    src_file: str
    action_params: dict = None


def get_function_params_class(func: Callable):
    """Inspects a playbook function's signature and returns the type of the param class if it exists"""
    func_signature = inspect.signature(func)
    if len(func_signature.parameters) == 1:
        return None
    parameter_name = list(func_signature.parameters)[1]
    return func_signature.parameters[parameter_name].annotation


def get_params_schema(func):
    action_params = get_function_params_class(func)
    if action_params is None:
        return None
    return action_params.schema()


def find_playbook_actions(scripts_root):
    python_files = glob.glob(f"{scripts_root}/*.py")

    for script in python_files:
        print(f"found playbook file: {script}")
        filename = os.path.basename(script)
        (module_name, ext) = os.path.splitext(filename)
        spec = importlib.util.spec_from_file_location(module_name, script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        playbooks = inspect.getmembers(
            module,
            lambda f: Action.is_action(f),
        )
        for _, func in playbooks:
            print("found playbook", func)
            action = Action(func)
            print("action", action)

            description = PlaybookDescription(
                function_name=func.__name__,
                builtin_trigger_params=func.__playbook["default_trigger_params"],
                docs=inspect.getdoc(func),
                src=inspect.getsource(func),
                src_file=inspect.getsourcefile(func),
                action_params=get_params_schema(func),
            )
            print(description.json(), "\n\n")


def main():
    parser = argparse.ArgumentParser(description="Generate playbook descriptions")
    parser.add_argument("--directory", type=str, help="directory containing the playbooks", default="./playbooks/robusta_playbooks")
    args = parser.parse_args()
    find_playbook_actions(args.directory)


if __name__ == "__main__":
    main()
