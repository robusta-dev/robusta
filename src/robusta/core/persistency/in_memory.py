# dummy persistence driver
from contextlib import contextmanager
from typing import Dict, Iterator, Type, TypeVar, cast

from pydantic import BaseModel

persistent_data: Dict[str, BaseModel] = {}

# TODO: we probably want some form of locking for this so two playbooks can't edit the same data at the same time
T = TypeVar("T", bound=BaseModel)


@contextmanager
def get_persistent_data(name: str, cls: Type[T]) -> Iterator[T]:
    try:
        data: T = cast(T, persistent_data.get(name, cls()))
        yield data
    finally:
        # write data back
        persistent_data[name] = data  # type: ignore
