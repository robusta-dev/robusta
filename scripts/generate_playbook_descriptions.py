import argparse
import importlib
import inspect
import os
import glob

from pydantic import BaseModel

from src.robusta import get_function_params_class
from src.robusta import TriggerParams
from src.robusta.runner import install_requirements


class PlaybookDescription(BaseModel):
    function_name: str
    builtin_trigger_params: TriggerParams
    docs: str = None
    src: str
    src_file: str
    action_params: dict = None


def get_params_schema(func):
    action_params = get_function_params_class(func)
    if action_params is None:
        return None
    return action_params.schema()


def load_scripts(scripts_root):
    install_requirements(os.path.join(scripts_root, 'requirements.txt'))

    python_files = glob.glob(f'{scripts_root}/*.py')

    for script in python_files:
        print(f'loading playbooks {script}')
        filename = os.path.basename(script)
        (module_name, ext) = os.path.splitext(filename)
        spec = importlib.util.spec_from_file_location(module_name, script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        playbooks = inspect.getmembers(module, lambda f: inspect.isfunction(f) and getattr(f, "__playbook", None) is not None)
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
    parser = argparse.ArgumentParser(description='Generate playbook descriptions')
    parser.add_argument('directory', type=str, help='directory containing the playbooks')
    args = parser.parse_args()
    load_scripts(args.directory)


if __name__ == "__main__":
    main()
