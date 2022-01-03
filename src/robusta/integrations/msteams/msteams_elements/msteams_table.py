from typing import List

from .msteams_colum import MsTeamsColumn
from .msteams_text_block import MsTeamsTextBlock
from .msteams_base import MsTeamsBase


class MsTeamsTable(MsTeamsBase):
    def __init__(self, headers: List[str], rows: List[List[str]]):

        column_element = self.__create_table(headers, rows)
        super().__init__(column_element.get_map_value())

    def __create_table(self, headers: List[str], rows: List[List[str]]) -> MsTeamsColumn:

        column_element = MsTeamsColumn()
        for index in range(len(headers)):
            single_column = [MsTeamsTextBlock(text=headers[index], weight="bolder")]
            single_column = single_column + self.__create_single_column_list(rows=rows, index=index)
            column_element.add_column(items=single_column, width_strech=True)

        return column_element

    def __create_single_column_list(self, rows: List[List[str]], index: int) -> List[map]:
        first_row = True
        column = []
        for row in rows:
            column.append(MsTeamsTextBlock(text=row[index], separator=first_row))
            first_row = False
        return column
