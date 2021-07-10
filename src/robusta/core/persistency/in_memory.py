# dummy persistence driver
from contextlib import contextmanager
from pydantic import BaseModel
from typing import Type, TypeVar, Dict, ContextManager

persistent_data: Dict[str, BaseModel] = {}

# TODO: we probably want some form of locking for this so two playbooks can't edit the same data at the same time
T = TypeVar("T", bound=BaseModel)


@contextmanager
def get_persistent_data(name: str, cls: Type[T]) -> ContextManager[T]:
    try:
        data = persistent_data.get(name, cls())
        yield data
    finally:
        # write data back
        persistent_data[name] = data
