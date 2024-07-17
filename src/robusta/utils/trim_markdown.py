try:
    from more_itertools import batched

def trim_markdown(text: str, max_length: int, suffix: str = "...") -> str:
    suffix_len = len(suffix)
    code_markdown_len = len('```')
    tuncate_index = max_length - suffix_len

    # if there is a code annotation near the end of the string
    if '```' in text[tuncate_index - code_markdown_len*2:tuncate_index]:
        tuncate_index = tuncate_index - code_markdown_len*2

    code_annotation_truncat_count = text.count('```', __start=tuncate_index)
    needs_end_markdown_string = (code_annotation_truncat_count % 2 == 1) # if there is an odd number of markdowns on the right
    if needs_end_markdown_string:
        return (text[:tuncate_index - code_markdown_len - suffix_len] + '```' + suffix)[:tuncate_index]
    else:
        return text[:tuncate_index - suffix_len] + suffix
