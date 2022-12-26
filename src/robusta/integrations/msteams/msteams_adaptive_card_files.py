from typing import Any, List

from robusta.core.reporting import FileBlock
from robusta.integrations.msteams.msteams_adaptive_card_files_image import MsTeamsAdaptiveCardFilesImage
from robusta.integrations.msteams.msteams_adaptive_card_files_text import MsTeamsAdaptiveCardFilesText


class MsTeamsAdaptiveCardFiles:
    def __init__(self):
        self.text_files = MsTeamsAdaptiveCardFilesText()

    # return List of MsTeamsBaseElement - cant return it in the constructor.
    def upload_files(self, file_blocks: List[FileBlock]) -> List[Any]:
        image_section_map = MsTeamsAdaptiveCardFilesImage().create_files_for_presentation(file_blocks)
        text_files_section_list = self.text_files.create_files_for_presentation(file_blocks)

        image_section_map_: List[Any] = [image_section_map] if image_section_map else []
        return text_files_section_list + image_section_map_

    # return the list of text containers with the list of lines, so later after
    # calculating the length of bytes left in the message, we can put the
    # lines evenly in each text container so we dont exceed the msg length
    def get_text_files_containers_list(self):
        return self.text_files.get_text_files_containers_list()
