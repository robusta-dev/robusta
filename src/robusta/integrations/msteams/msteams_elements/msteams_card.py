from typing import List

from .msteams_base import MsTeamsBase


class MsTeamsCard(MsTeamsBase):
    def __init__(self, elements: List[MsTeamsBase]):
        content = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.2",
            "msTeams": {
                "width": "full"
            },
            "body": [elem.get_map_value() for elem in elements]
        }

        attachment = {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "contentUrl": None,
            "content": content
        }

        block = {
            "type": "message",
            "attachments": [attachment]
        }

        super().__init__(block)
