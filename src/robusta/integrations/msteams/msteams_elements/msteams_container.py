from typing import List

from .msteams_base import MsTeamsBase


class MsTeamsContainer(MsTeamsBase):
    
    def __init__(self, key: str, elements: List[MsTeamsBase]):
        super().__init__(self.__container(key, elements))

    def __container(self, key: str, elements: List[MsTeamsBase]):
        block = {
            'type': "Container",
            "style": "accent",
            "isVisible": False,
            "bleed": False,
            "items": self.__get_items(elements),
        }
        if key is not None:
            block["id"] = key
        return block

    @classmethod
    def __get_items(cls, elements: List[MsTeamsBase]):
        return [elem.get_map_value() for elem in elements]
