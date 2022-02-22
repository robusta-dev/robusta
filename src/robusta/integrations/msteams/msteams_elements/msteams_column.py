from typing import List

from .msteams_base import MsTeamsBase
from .msteams_action import MsTeamsAction


class MsTeamsColumn(MsTeamsBase):
    def __init__(self) -> None:
        self.column_list = []
        super().__init__(self.__column_set())

    def __column_set(self) -> map:
        return {
            "type": "ColumnSet",
            "columns": self.column_list
        }

    def add_column(
        self,
        items: List[MsTeamsBase],
        width_stretch: bool = False,
        is_visible: bool = True,
        key: str = None,
        action: MsTeamsAction = None,
    ):
        block = {
            "type": "Column",
            "width": "stretch" if width_stretch else "auto",
            "isVisible": is_visible,
            "items": self.__to_map_list(items),
        }

        if key is not None:
            block["id"] = key
        if action is not None:
            block.update(action.get_map_value())

        self.column_list.append(block)

    def __to_map_list(self, elements: List[MsTeamsBase]) -> List[dict]:
        return [element.get_map_value() for element in elements]
