from typing import List

from .blocks import *


def add_pngs_for_all_svgs(blocks: List[FileBlock]):
    # we import cairosvg here and not globally because in some environments it isn't trivially installed (e.g. windows)
    # and we don't want to throw an exception globally when it isn't around
    import cairosvg

    new_blocks = blocks.copy()
    for b in blocks:
        if not isinstance(b, FileBlock):
            continue
        if not b.filename.endswith(".svg"):
            continue
        conversion = cairosvg.svg2png(bytestring=b.contents)
        new_blocks.append(FileBlock(b.filename.replace(".svg", ".png"), conversion))
    return new_blocks
