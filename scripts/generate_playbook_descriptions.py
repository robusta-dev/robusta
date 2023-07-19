# This script loads and inspects playbooks from a given directory. It defines a `PlaybookDescription` class that stores information about a playbook function,
#including its name, documentation, source code, and parameters. The script also includes functions for inspecting the signature of a playbook function to extract information about its parameters and generating a JSON schema for the parameters.
# The `load_scripts` function takes in the path to the root directory containing the playbooks as an argument. 
#It searches for all Python files in the directory and attempts to load them as modules. For each loaded module, it searches for functions that have been decorated with the `__playbook` attribute and extracts information about them using the `PlaybookDescription` class. 
#The resulting descriptions are printed to the console in JSON format.
# The `main` function sets up an argument parser to accept the path to the playbooks directory as a command-line argument and calls the `load_scripts` function with the provided path.
# This script can be used to generate documentation for a collection of playbooks by providing it with the path to the directory containing the playbooks. 
#The resulting JSON output can be further processed to generate human-readable documentation in various formats.


import argparse
import glob
import importlib
import inspect
import os
from typing import Callable

from pydantic import BaseModel


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


def load_scripts(scripts_root):
    # install_requirements(os.path.join(scripts_root, 'requirements.txt'))

    python_files = glob.glob(f"{scripts_root}/*.py")

    for script in python_files:
        print(f"loading playbooks {script}")
        filename = os.path.basename(script)
        (module_name, ext) = os.path.splitext(filename)
        spec = importlib.util.spec_from_file_location(module_name, script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        playbooks = inspect.getmembers(
            module,
            lambda f: inspect.isfunction(f) and getattr(f, "__playbook", None) is not None,
        )
        for _, func in playbooks:
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
    # TODO Arik - Need to be fixed in order to expose actions schema
    parser = argparse.ArgumentParser(description="Generate playbook descriptions")
    parser.add_argument("directory", type=str, help="directory containing the playbooks")
    args = parser.parse_args()
    load_scripts(args.directory)


if __name__ == "__main__":
    main()
