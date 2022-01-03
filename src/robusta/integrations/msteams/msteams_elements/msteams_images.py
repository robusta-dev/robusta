from typing import List

from ....core.model.env_vars import TEAMS_IMAGE_WIDTH
from .msteams_base import MsTeamsBase


class MsTeamsImages(MsTeamsBase):
    def __init__(self, encoded_images: List[str]):
        self.images_len_in_bytes = 0
        image_elements = [self.__to_image(img) for img in encoded_images]
        super().__init__(self.__to_image_set(image_elements))

    def get_images_len_in_bytes(self):
        return self.images_len_in_bytes

    @classmethod
    def __to_image_set(cls, image_elements: List[dict]) -> dict:
        return {
                    "type": "ImageSet",
                    "imageSize": "large",
                    "images": image_elements
                }

    def __to_image(self, encoded_image: str) -> dict:
        self.images_len_in_bytes += len(encoded_image)
        return {
            "type": "Image",
            "url": encoded_image,
            "width": TEAMS_IMAGE_WIDTH
        }
