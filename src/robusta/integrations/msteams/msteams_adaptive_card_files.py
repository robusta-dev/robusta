from typing import List

from .msteams_adaptive_card_files_image import MsTeamsAdaptiveCardFilesImage
from .msteams_adaptive_card_files_text import MsTeamsAdaptiveCardFilesText
from ...core.reporting import FileBlock


class MsTeamsAdaptiveCardFiles():

    def __init__(self):
        self.text_files = MsTeamsAdaptiveCardFilesText()

    # return List of MsTeamsBaseElement - cant return it in the constructor.
    def upload_files(self, file_blocks: List[FileBlock]) -> List[map]:
        image_section_map: map = MsTeamsAdaptiveCardFilesImage().create_files_for_presentation(file_blocks)
        text_files_section_list = self.text_files.create_files_for_presentation(file_blocks)

        if image_section_map:
            image_section_map = [image_section_map]
        else:
            image_section_map = []
        return text_files_section_list + image_section_map

    # return the list of text containers with the list of lines, so later after
    # calculating the length of bytes left in the message, we can put the 
    # lines evenly in each text container so we dont exceed the msg length
    def get_text_files_containers_list(self):
        return self.text_files.get_text_files_containers_list()