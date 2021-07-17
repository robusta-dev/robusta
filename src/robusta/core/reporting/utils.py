from typing import List

from .blocks import *


def convert_svg_to_png(svg: bytes) -> bytes:
    # we import cairosvg here and not globally because in some environments it isn't trivially installed (e.g. windows)
    # and we don't want to throw an exception globally when it isn't around
    import cairosvg

    return cairosvg.svg2png(bytestring=svg)


def add_pngs_for_all_svgs(blocks: List[FileBlock]):
    new_blocks = blocks.copy()
    for b in blocks:
        if not isinstance(b, FileBlock):
            continue
        if not b.filename.endswith(".svg"):
            continue
        conversion = convert_svg_to_png(b.contents)
        new_blocks.append(FileBlock(b.filename.replace(".svg", ".png"), conversion))
    return new_blocks
