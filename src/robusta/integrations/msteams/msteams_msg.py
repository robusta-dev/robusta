import json
import logging
import requests
from typing import List

from .msteams_elements.msteams_base import MsTeamsBase
from .msteams_adaptive_card_files import MsTeamsAdaptiveCardFiles
from .msteams_elements.msteams_table import MsTeamsTable
from .msteams_elements.msteams_text_block import MsTeamsTextBlock
from .msteams_elements.msteams_colum import MsTeamsColumn
from .msteams_elements.msteams_card import MsTeamsCard
from .msteams_elements.msteams_images import MsTeamsImages
from ...core.reporting import FileBlock, TableBlock, ListBlock, MarkdownBlock, KubernetesDiffBlock, HeaderBlock


class MsTeamsMsg:
    # actual size according to the DOC is ~28K.
    # it's hard to determine the real size because for example there can be large images that doesn't count
    # and converting the map to json doesn't give us an exact indication of the size so we need to take 
    # a safe zone of less then 28K
    MAX_SIZE_IN_BYTES = (1024 * 20)

    def __init__(self, webhook_url: str):
        self.entire_msg: List[MsTeamsBase] = []
        self.current_section: List[MsTeamsBase] = []
        self.text_file_containers = []
        self.webhook_url = webhook_url

    def write_title_and_desc(self, title: str, description: str, severity: str,
                             platform_enabled: bool, investigate_uri: str):
        block = MsTeamsTextBlock(text=f"{severity} - {title}", font_size='extraLarge')
        self.__write_to_entire_msg([block])
        if platform_enabled:  # add link to the Robusta ui, if it's configured
            self.__write_to_entire_msg([MsTeamsTextBlock(text=f"<{investigate_uri}|Investigate>")])

        if description is not None:
            block = MsTeamsTextBlock(text=description)
            self.__write_to_entire_msg([block])

    def write_current_section(self):
        if len(self.current_section) == 0:
            return

        space_block = MsTeamsTextBlock(text=' ', font_size='small')
        separator_block = MsTeamsTextBlock(text=' ', separator=True)

        underline_block = MsTeamsColumn()
        underline_block.add_column(items=[space_block, separator_block], width_strech=True)

        self.__write_to_entire_msg([underline_block])
        self.__write_to_entire_msg(self.current_section)
        self.current_section = []

    def __write_to_entire_msg(self, blocks: List[MsTeamsBase]):
        self.entire_msg += blocks

    def __write_to_current_section(self, blocks: List[MsTeamsBase]):
        self.current_section += blocks

    def __sub_section_separator(self):
        if len(self.current_section) == 0:
            return
        space_block = MsTeamsTextBlock(text=' ', font_size='small')
        separator_block = MsTeamsTextBlock(text='_' * 30, font_size='small', horizontal_alignment='center')
        self.__write_to_current_section([space_block,separator_block,space_block,space_block])

    def upload_files(self, file_blocks: List[FileBlock]):
        msteams_files = MsTeamsAdaptiveCardFiles()
        block_list: List[MsTeamsBase] = msteams_files.upload_files(file_blocks)
        if len(block_list) > 0:
            self.__sub_section_separator()

        self.text_file_containers += msteams_files.get_text_files_containers_list()
        
        self.__write_to_current_section(block_list)

    def table(self, table_block : TableBlock):
        msteam_table = MsTeamsTable(list(table_block.headers), table_block.rows)
        self.__write_to_current_section([msteam_table])
    
    def items_list(self, block: ListBlock):
        self.__sub_section_separator()
        for line in block.items:
            bullet_lines = '\n- ' + line + '\n'
            self.__write_to_current_section([MsTeamsTextBlock(bullet_lines)])

    def diff(self, block: KubernetesDiffBlock):
        rows = [f"*{diff.formatted_path}*: {diff.other_value} -> {diff.value}" for diff in block.diffs]

        list_blocks = ListBlock(rows)
        self.items_list(list_blocks)

    def markdown_block(self, block: MarkdownBlock):
        if not block.text:
            return
        self.__write_to_current_section([MsTeamsTextBlock(block.text)])

    def divider_block(self):
        self.__write_to_current_section([MsTeamsTextBlock('\n\n')])

    def header_block(self, block: HeaderBlock):
        current_header_string = block.text + '\n\n'
        self.__write_to_current_section([MsTeamsTextBlock(current_header_string, font_size='large')])

    # dont include the base 64 images in the total size calculation
    def _put_text_files_data_up_to_max_limit(self, complete_card_map: map):
        curr_images_len = 0
        for element in self.entire_msg:
            if isinstance(element, MsTeamsImages):
                curr_images_len += element.get_images_len_in_bytes()

        max_len_left = self.MAX_SIZE_IN_BYTES - (self.__get_current_card_len(complete_card_map) - curr_images_len)

        curr_line = 0
        while True:
            line_added = False
            curr_line += 1
            for text_element, lines in self.text_file_containers:
                if len(lines) < curr_line:
                    continue

                line = lines[len(lines) - curr_line]
                max_len_left -= len(line)
                if max_len_left < 0:
                    return
                new_text_value = line + text_element.get_text_from_block()
                text_element.set_text_from_block(new_text_value)
                line_added = True

            if not line_added:
                return

    def send(self):
        try:
            complete_card_map: dict = MsTeamsCard(self.entire_msg).get_map_value()
            self._put_text_files_data_up_to_max_limit(complete_card_map)

            response = requests.post(self.webhook_url, json=complete_card_map)
            if response.status_code not in [200, 201]:
                logging.error(f"Error sending to ms teams json: {complete_card_map} error: {response.reason}")

            if response.text and "error" in response.text.lower():  # teams error indication is in the text only :(
                logging.error(f"Failed to send message to teams. error: {response.text} message: {complete_card_map}")

        except Exception as e:
            logging.error(f"error sending message to msteams\ne={e}\n")   

    @classmethod
    def __get_current_card_len(cls, complete_card_map: dict):
        return len(json.dumps(complete_card_map, ensure_ascii=True, indent=2))
