import uuid

from typing import List

from .msteams_elements.msteams_text_block import MsTeamsTextBlock
from .msteams_elements.msteams_action import MsTeamsAction
from .msteams_elements.msteams_column import MsTeamsColumn
from .msteams_elements.msteams_container import MsTeamsContainer

from ...core.reporting import FileBlock

'''
there are 3 elements for each text file":
1. row that contains 'open file-name' , and 'close file-name' buttons. 
   the open is visible and the close is invisible at init stage
2. container that contains the last lines of the file - invisible at the init stage
3. row that contains 'close file-name' buttons, invisible at init stage

when a open button is pressed for specific file, the close file for the current file become visible, 
and also the container presenting the file text. for all the other files, the 'open file-name' buttons 
become visible and all the other buttons become invisible

no point in creating object for each file since it will only hold a few variables such as the file name
 and keys and the logic is mainly to create the columns and text containers for all the files combine
'''


class MsTeamsAdaptiveCardFilesText:

    def __init__(self):
        self.open_key_list = []
        self.close_start_key_list = []
        self.close_end_key_list = []
        self.text_file_presentation_key_list = []

        self.open_text_list = []
        self.close_start_text_list = []
        self.close_end_text_list = []
        self.text_file_presentation_list = []

        self.action_open_text_list = []
        self.action_close_start_text_list = []
        self.action_close_end_text_list = []

        self.file_name_list = []

        self.text_map_and_single_text_lines_list = []

    def create_files_for_presentation(self, file_blocks: List[FileBlock]) -> List[map]:
        file_content_list = []

        for file_block in file_blocks:
            if not self.__is_txt_file(file_block.filename):
                continue
            self.__create_new_keys()
            self.file_name_list.append(file_block.filename)
            file_content_list.append(file_block.contents)

        if len(self.open_key_list) == 0:
            return []

        for index in range(len(self.open_key_list)):
            self.__manage_blocks_for_single_file(index, self.file_name_list[index], file_content_list[index])
        return self.__manage_all_text_to_send()

    def get_text_files_containers_list(self):
        return self.text_map_and_single_text_lines_list

    def __create_new_keys(self):
        self.open_key_list.append(str(uuid.uuid4()))
        self.close_start_key_list.append(str(uuid.uuid4()))
        self.close_end_key_list.append(str(uuid.uuid4()))
        self.text_file_presentation_key_list.append(str(uuid.uuid4()))

    def __manage_blocks_for_single_file(self, index, file_name : str, content : bytes):
        open_text_action = self.__action(index, open=True, title='press to open')
        close_text_action = self.__action(index, open=False, title='press to close')

        open_text = MsTeamsTextBlock('***open ' + file_name + '***', is_subtle=False)
        close_start = MsTeamsTextBlock('***close ' + file_name + '***', is_subtle=False)
        close_end = MsTeamsTextBlock('***close ' + file_name + '***', is_subtle=False)

        self.open_text_list.append(open_text)
        self.close_start_text_list.append(close_start)
        self.close_end_text_list.append(close_end)

        self.action_open_text_list.append(open_text_action)
        self.action_close_start_text_list.append(close_text_action)
        self.action_close_end_text_list.append(close_text_action)

        self.text_file_presentation_list.append(self.__present_text_file_block(self.text_file_presentation_key_list[index], content.decode('utf-8')))

    def __manage_all_text_to_send(self):
        top_column_set = MsTeamsColumn()
        bottom_column_set = MsTeamsColumn()
        for index in range(len(self.open_text_list)):
            top_column_set.add_column(key=self.open_key_list[index],
                                      items=[self.open_text_list[index]],
                                      action= self.action_open_text_list[index])

            top_column_set.add_column(is_visible=False,
                                      key=self.close_start_key_list[index],
                                      items=[self.close_start_text_list[index]],
                                      action=self.action_close_start_text_list[index])

            # spaces between files
            top_column_set.add_column(items=[MsTeamsTextBlock(' ')])
            top_column_set.add_column(items=[MsTeamsTextBlock(' ')])

            bottom_column_set.add_column(is_visible=False,
                                         key=self.close_end_key_list[index],
                                         items=[self.close_end_text_list[index]],
                                         action=self.action_close_end_text_list[index])
        
        list_to_return = [top_column_set]
        list_to_return += self.text_file_presentation_list
        list_to_return.append(bottom_column_set)

        return list_to_return
    
    def __action(self, index, open: bool, title: str) -> map:
        visible_elements_map = {False: [], True: []}
        curr_key = self.open_key_list[index]
        for key in self.open_key_list:
            visible = (not open) or (curr_key != key)
            visible_elements_map[visible].append(key)

        curr_key = self.close_start_key_list[index]
        for key in self.close_start_key_list:
            visible = open and (curr_key == key)
            visible_elements_map[visible].append(key)

        curr_key = self.close_end_key_list[index]
        for key in self.close_end_key_list:
            visible = open and (curr_key == key)
            visible_elements_map[visible].append(key)

        curr_key = self.text_file_presentation_key_list[index]
        for key in self.text_file_presentation_key_list:
            visible = open and (curr_key == key)
            visible_elements_map[visible].append(key)

        return MsTeamsAction(title, visible_keys=visible_elements_map[True], invisible_keys=visible_elements_map[False])

    # there is a limit to the number of letters you can write - dont know what it is !!!
    # /t doesn't work so we need to simulate spaces (which are trimmed so we use '. . . ')
    def __present_text_file_block(self, key: str, text: str):
        text_lines_list = []
        new_text = text.replace('\t', '. . . ')

        for line in new_text.split('\n'):
            text_lines_list.append(line + '\n\n')

        # will be completed later
        text_block = MsTeamsTextBlock('', wrap=True, weight='bolder', is_visible=True)
        self.text_map_and_single_text_lines_list.append([text_block, text_lines_list])
        return MsTeamsContainer(key=key, elements=[text_block])

    @classmethod
    def __is_txt_file(cls, file_name: str) -> bool:
        txt_suffixes = ['.txt', '.json', '.yaml', '.log']
        for prefix in txt_suffixes:
            if file_name.lower().endswith(prefix):
                return True
        return False
