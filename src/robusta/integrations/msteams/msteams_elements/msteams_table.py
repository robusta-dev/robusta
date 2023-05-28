from typing import List, Optional

from robusta.integrations.msteams.msteams_elements.msteams_base import MsTeamsBase
from robusta.integrations.msteams.msteams_elements.msteams_text_block import MsTeamsTextBlock


class MsTeamsTable(MsTeamsBase):
    def __init__(self, headers: List[str], rows: List[List[str]], col_width: Optional[List[int]]):
        super().__init__(self.getTable(headers, rows, col_width))

    def getTableCell(self, text: str):
        return {"type": "TableCell", "items": [MsTeamsTextBlock(text).get_map_value()]}

    def getTableRow(self, row: List[str]):
        return {"type": "TableRow", "cells": [self.getTableCell(i) for i in row]}

    def getTable(self, headers: List[str], rows: List[List[str]], col_width: Optional[List[int]]):
        combined_rows = [headers, *rows]
        widths = col_width if col_width else [1] * len(headers)
        return {
            "type": "Table",
            "columns": [{"width": size} for size in widths],
            "rows": [self.getTableRow(r) for r in combined_rows],
        }
