import argparse
import importlib
import inspect
import os
import glob
import json
import typer
from typing import Callable
from robusta.core.playbooks.actions_registry import Action
from robusta.runner.config_loader import ConfigLoader

app = typer.Typer()


def document_playbooks(scripts_root):
    ConfigLoader.install_requirements(os.path.join(scripts_root, "requirements.txt"))

    python_files = glob.glob(f"{scripts_root}/*.py")
    result = {}

    for script in python_files:
        print(f"loading playbooks {script}")
        filename = os.path.basename(script)
        (module_name, ext) = os.path.splitext(filename)
        spec = importlib.util.spec_from_file_location(module_name, script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        playbooks = inspect.getmembers(
            module,
            Action.is_action,
        )
        for _, func in playbooks:
            action = Action(func)
            data = {"event_type": action.event_type.__name__}
            if action.params_type:
                data["params_type"] = action.params_type.schema()
            result[action.action_name] = data
    return result


@app.command()
def run(playbooks_dir: str, output_path: str):
    result = document_playbooks(playbooks_dir)
    with open(output_path, "w") as f:
        f.write(json.dumps(result))


if __name__ == "__main__":
    app()
