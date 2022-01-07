from typing import List

from .msteams_base import MsTeamsBase


class MsTeamsAction(MsTeamsBase):
    def __init__(self, title: str, visible_keys: List[str], invisible_keys: List[str]):
        super().__init__(self.__to_action(title, visible_keys, invisible_keys))

    @classmethod
    def __to_action(cls, title: str, visible_keys: List[str], invisible_keys: List[str]):
        return {
            "selectAction": {
                "type": "Action.ToggleVisibility",
                "title": title,
                "targetElements": cls.__action_toggle_target_elements(visible_keys, invisible_keys),
            }
        }

    @classmethod
    def __action_toggle_target_elements(cls, visible_keys: List[str], invisible_keys: List[str]) -> List[dict]:
        actions = cls.__set_toggle_action(visible_keys, True)
        actions.extend(cls.__set_toggle_action(invisible_keys, False))
        return actions

    @classmethod
    def __set_toggle_action(cls, keys: List[str], visible: bool) -> List[dict]:
        return [{"elementId": key, "isVisible": visible} for key in keys]
