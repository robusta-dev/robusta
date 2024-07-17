import pytest

from robusta.core.sinks.transformer import Transformer


@pytest.mark.parametrize(
    "max_length,expected_output", [
        (9, "```...```"),
        (10, "```t...```"),
        (13, "```test...```"),
        (16, "```testing...```"),
        (28, "```testing 12345667 so...```"),
        (29, "```testing 12345667 som...```"),
        (31, "```testing 12345667 some ...```"),
        (35, "```testing 12345667 some more...```"),
        (36, "```testing 12345667 some more ...```"),
        (37, "```testing 12345667 some more text```"),
        (53, "```testing 12345667 some more text```"),
        (54, "```testing 12345667 some more text```"),
        (111, "```testing 12345667 some more text```"),
    ])
def test_trim_markdown(max_length: int, expected_output: str):
    text = "```testing 12345667 some more text```"
    trimmed = Transformer.trim_markdown(text, max_length, "...")
    assert trimmed == expected_output
    assert len(trimmed) <= max_length

@pytest.mark.parametrize(
    "max_length,expected_output", [
        (9, "```...```"),
        (10, "```t...```"),
        (13, "```test...```"),
        (31, "```testing 12345667 some ...```"),
        (36, "```testing 12345667 some more ...```"),

        # edge case, last few characters contains a partial codeblock '`'
        # we cut off a few extra characters so we dont accidentally write ````
        (37, "```testing 12345667 some...```"),
        (38, "```testing 12345667 some ...```"),
        (39, "```testing 12345667 some m...```"),

        (40, "```testing 12345667 some more text```..."),
        (43, "```testing 12345667 some more text``` so..."),
        (52, "```testing 12345667 some more text``` some text a..."),
        (53, "```testing 12345667 some more text``` some text af..."),
        (54, "```testing 12345667 some more text``` some text aft..."),
        (76, "```testing 12345667 some more text``` some text after stuff sdkljhadsflka..."),
        (77, "```testing 12345667 some more text``` some text after stuff sdkljhadsflkas..."),
        (78, "```testing 12345667 some more text``` some text after stuff sdkljhadsflkashdfl"),
        (100, "```testing 12345667 some more text``` some text after stuff sdkljhadsflkashdfl"),
    ])
def test_trim_markdown_with_text(max_length: int, expected_output: str):
    text = "```testing 12345667 some more text``` some text after stuff sdkljhadsflkashdfl"
    trimmed = Transformer.trim_markdown(text, max_length, "...")
    print(f"{trimmed}")
    assert trimmed == expected_output
    assert len(trimmed) <= max_length


@pytest.mark.parametrize(
    "max_length,expected_output", [
        (3, "$$$"),
        (4, "N$$$"),
        (5, "No$$$"),
        (10, "No code$$$"),
        (41, "No code blocks whatsoever in this text"),
        (42, "No code blocks whatsoever in this text"),
        (111, "No code blocks whatsoever in this text"),
    ]
)
def test_trim_markdown_no_code_blocks(max_length: int, expected_output: str):
    text = "No code blocks whatsoever in this text"
    trimmed = Transformer.trim_markdown(text, max_length, "$$$")
    assert trimmed == expected_output
    assert len(trimmed) <= max_length
