try:
    from itertools import batched
except ImportError:  # Python < 3.12
    from more_itertools import batched

import regex


def trim_markdown(text: str, max_length: int, suffix: str = "...") -> str:
    # This method of trimming markdown is not universal. It only takes care of correctly
    # trimming block sections. Implementing a general truncation method for markdown that
    # would handle all the possible tags in a correct way would be rather complex.

    trim_idx = max_length - len(suffix)

    if trim_idx <= 0:  # The pathological cases.
        return suffix[:max_length]

    # Process block quotes backwards in the input
    for match_open, match_close in batched(regex.finditer("```", text, regex.REVERSE), 2):
        open_start, open_end = match_close.span()
        close_start, close_end = match_open.span()
        if trim_idx >= close_end:
            # Trimming point after this block quote
            return text[:trim_idx] + suffix
        if trim_idx < open_start:
            # Trimming point before this block quote - continue to the preceding block
            continue
        if trim_idx >= open_start and trim_idx < open_start + 3:
            # Trimming point inside the opening block quote tag
            return text[:trim_idx].rstrip("`") + suffix
        if trim_idx >= close_start and trim_idx < close_end:
            # Trimming point inside the closing block quote tag
            if trim_idx - open_end >= 3:  # Enough space to insert the closing tag
                return text[:trim_idx - 3] + "```" + suffix
            else:  # Not enough space, strip the whole block
                return text[:open_start] + suffix
        if trim_idx >= open_end and trim_idx < close_start:
            # Trimming point inside the block quote
            if trim_idx - open_end >= 3:  # Enough space to insert the closing tag
                return text[:trim_idx - 3] + "```" + suffix
            else:  # Not enough space, strip the whole block
                return text[:open_start] + suffix
