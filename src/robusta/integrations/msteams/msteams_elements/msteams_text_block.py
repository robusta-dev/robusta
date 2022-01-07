from .msteams_base import MsTeamsBase
from ..msteams_mark_down_fix_url import MsTeamsMarkDownFixUrl


class MsTeamsTextBlock(MsTeamsBase):
    def __init__(self,
                 text : str,
                 is_subtle : bool = None,
                 wrap: bool = None,
                 weight: str = None,
                 is_visible : bool = True,
                 separator : bool = False,
                 font_size : str = 'medium',
                 horizontal_alignment : str = "left"
                 ):
        super().__init__(self.__text_block(text, is_subtle, wrap, weight, is_visible,
                                           separator, font_size, horizontal_alignment))

    def __to_msteams_text(self, text: str) -> str:
        teams_text = MsTeamsMarkDownFixUrl().fix_text(text)
        teams_text = teams_text.replace("```", "")
        return teams_text

    def __text_block(self,
                     text: str,
                     is_subtle: bool = None,
                     wrap: bool = None,
                     weight: str = None,
                     is_visible: bool = True,
                     separator: bool = False,
                     font_size: str = 'medium',
                     horizontal_alignment: str = "left"
                     ):
        self.block = {
            "type": "TextBlock",
            "text": self.__to_msteams_text(text),
            "size": font_size,
            "wrap": True,
        }

        if not is_visible:
            self.block["isVisible"] = is_visible

        if separator:
            self.block["separator"] = separator

        if horizontal_alignment != "left":
            self.block["horizontalAlignment"] = horizontal_alignment

        if is_subtle is not None:
            self.block["isSubtle"] = is_subtle

        if weight is not None:
            self.block["weight"] = weight

        return self.block

    def get_text_from_block(self) -> str:
        return self.block["text"]

    def set_text_from_block(self, text: str):
        self.block["text"] = text


