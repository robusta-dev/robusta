from typing import List

from .blocks import *
import cairosvg  # type: ignore


def add_pngs_for_all_svgs(blocks: List[FileBlock]):
    new_blocks = blocks.copy()
    for b in blocks:
        if not isinstance(b, FileBlock):
            continue
        if not b.filename.endswith(".svg"):
            continue
        conversion = cairosvg.svg2png(bytestring=b.contents)
        new_blocks.append(FileBlock(b.filename.replace(".svg", ".png"), conversion))
    return new_blocks
