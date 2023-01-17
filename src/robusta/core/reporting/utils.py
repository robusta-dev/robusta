import logging
from typing import List, Optional

from robusta.core.reporting.blocks import FileBlock

JPG_SUFFIX = ".jpg"
PNG_SUFFIX = ".png"
SVG_SUFFIX = ".svg"


def file_suffix_match(file_name: str, suffix: str) -> bool:
    return file_name.lower().endswith(suffix)


def is_image(file_name: str):
    return (
        file_suffix_match(file_name, JPG_SUFFIX)
        or file_suffix_match(file_name, PNG_SUFFIX)
        or file_suffix_match(file_name, SVG_SUFFIX)
    )


def convert_svg_to_png(svg: bytes) -> Optional[bytes]:
    # we import cairosvg here and not globally because in some environments it isn't trivially installed (e.g. windows)
    # and we don't want to throw an exception globally when it isn't around
    import cairosvg

    try:
        return cairosvg.svg2png(bytestring=svg)
    except Exception:
        logging.error(f"error converting svg to png; svg={svg}")
        return None


def add_pngs_for_all_svgs(blocks: List[FileBlock]):
    new_blocks = blocks.copy()
    for b in blocks:
        if not isinstance(b, FileBlock):
            continue
        if not b.filename.endswith(".svg"):
            continue
        conversion = convert_svg_to_png(b.contents)
        if conversion is None:
            continue
        new_blocks.append(FileBlock(b.filename.replace(".svg", ".png"), conversion))
    return new_blocks
