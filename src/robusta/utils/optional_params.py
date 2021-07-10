import inspect
import logging
from typing import Callable, Dict


# TODO: could be extracted to a small library - see e.g. https://stackoverflow.com/questions/16576553/python-only-pass-arguments-if-the-variable-exists
def call_with_optional_params(func: Callable, available_args: Dict[str, object]):
    args_to_use = []  # must be in order
    expected_args = inspect.getfullargspec(func)
    for arg_name in expected_args.args + expected_args.kwonlyargs:
        if arg_name in available_args:
            args_to_use.append(available_args[arg_name])
        else:
            raise Exception(
                f"function requires argument that we don't recognize by name {arg_name}"
            )
    logging.info(
        f"available_args={available_args} expected_args={expected_args} args_to_use=f{args_to_use}"
    )
    return func(*args_to_use)
