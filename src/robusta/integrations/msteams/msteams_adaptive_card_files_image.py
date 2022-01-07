import tempfile
import base64
import os
import uuid
from PIL import Image

from ...core.reporting.blocks import *
from .msteams_elements.msteams_images import MsTeamsImages
from cairosvg import svg2png

JPG_SUFFIX = ".jpg"
PNG_SUFFIX = ".png"
SVG_SUFFIX = ".svg"


class MsTeamsAdaptiveCardFilesImage:

    @classmethod
    def create_files_for_presentation(cls, file_blocks: List[FileBlock]) -> map:
        encoded_images = []
        image_file_blocks = [file_block for file_block in file_blocks if cls.__is_image(file_block.filename)]
        for image_file_block in image_file_blocks:
            encoded_images.append(
                cls.__convert_bytes_to_base_64_url(image_file_block.filename, image_file_block.contents)
            )

        if len(encoded_images) == 0:
            return []
        return MsTeamsImages(encoded_images)

    @classmethod
    def __get_tmp_file_path(cls):
        return os.path.join(tempfile.gettempdir(), str(uuid.uuid1()))

    @classmethod
    def __file_suffix_match(cls, file_name: str, suffix: str) -> bool:
        return file_name.lower().endswith(suffix)

    @classmethod
    def __is_image(cls, file_name: str):
        return cls.__file_suffix_match(file_name, JPG_SUFFIX) \
            or cls.__file_suffix_match(file_name, PNG_SUFFIX) \
            or cls.__file_suffix_match(file_name, SVG_SUFFIX)

    @classmethod
    def __convert_bytes_to_base_64_url(cls, file_name: str, image_bytes: bytes):
        if cls.__file_suffix_match(file_name, JPG_SUFFIX):
            return cls.__jpg_convert_bytes_to_base_64_url(image_bytes)
        if cls.__file_suffix_match(file_name, PNG_SUFFIX):
            return cls.__png_convert_bytes_to_base_64_url(image_bytes)
        return cls.__svg_convert_bytes_to_jpg(image_bytes)

    @classmethod
    def __jpg_convert_bytes_to_base_64_url(cls, jpg_bytes: bytes):
        b64_string = base64.b64encode(jpg_bytes).decode("utf-8")
        return 'data:image/jpeg;base64,{0}'.format(b64_string)

    # msteams cant read parsing of url to 'data:image/png;base64,...
    @classmethod
    def __png_convert_bytes_to_base_64_url(cls, png_bytes : bytes):
        png_file_path = cls.__get_tmp_file_path() + PNG_SUFFIX
        jpg_file_path = cls.__get_tmp_file_path() + JPG_SUFFIX
        with open(png_file_path, 'wb') as f:
            f.write(png_bytes)

        im = Image.open(png_file_path)
        rgb_im = im.convert('RGB')
        rgb_im.save(jpg_file_path)
        with open(jpg_file_path, 'rb') as f:
            jpg_bytes = f.read()

        os.remove(png_file_path)
        os.remove(jpg_file_path)

        return cls.__jpg_convert_bytes_to_base_64_url(jpg_bytes)

    # msteams cant read parsing of url to svg image
    @classmethod
    def __svg_convert_bytes_to_jpg(cls, svg_bytes : bytes):
        return cls.__png_convert_bytes_to_base_64_url(svg2png(bytestring=svg_bytes))