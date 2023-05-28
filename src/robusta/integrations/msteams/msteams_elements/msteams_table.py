from typing import List

from robusta.integrations.msteams.msteams_elements.msteams_base import MsTeamsBase
from robusta.integrations.msteams.msteams_elements.msteams_text_block import MsTeamsTextBlock


class MsTeamsTable(MsTeamsBase):
    def __init__(self, headers: List[str], rows: List[List[str]]):

        super().__init__(self.getTable(headers, rows))

    def getTableCell(self, text: str):
        return {"type": "TableCell", "items": [MsTeamsTextBlock(text).get_map_value()]}

    def getTableRow(self, row: List[str]):
        return {"type": "TableRow", "cells": [self.getTableCell(i) for i in row]}

    def getTable(self, headers: List[str], rows: List[List[str]]):
        combined_rows = [headers, *rows]
        return {
            "type": "Table",
            "columns": [{"width": 1} for _ in headers],
            "rows": [self.getTableRow(r) for r in combined_rows],
        }
