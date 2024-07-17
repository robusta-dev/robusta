import pytest

from robusta.core.sinks.transformer import Transformer


@pytest.mark.parametrize(
    "max_length,expected_output", [
        (0, ""),
        (1, "#"),
        (2, "##"),
        (3, "##"),
        (4, "##"),
        (5, "##"),
        (6, "##"),
        (7, "##"),
        (8, "``````##"),
        (9, "```o```##"),
        (10, "```oh```##"),
        (13, "```oh``` he##"),
        (16, "```oh``` hello##"),
        (17, "```oh``` hello ##"),
        (18, "```oh``` hello ##"),
        (19, "```oh``` hello ##"),
        (20, "```oh``` hello ##"),
        (21, "```oh``` hello ##"),
        (22, "```oh``` hello ##"),
        (23, "```oh``` hello ``````##"),
        (24, "```oh``` hello ```w```##"),
        (25, "```oh``` hello ```wo```##"),
        (27, "```oh``` hello ```worl```##"),
        (28, "```oh``` hello ```world```##"),
        (29, "```oh``` hello ```world``` ##"),
        (31, "```oh``` hello ```world``` an##"),
        (39, "```oh``` hello ```world``` and then ##"),
        (42, "```oh``` hello ```world``` and then ##"),
        (44, "```oh``` hello ```world``` and then ``````##"),
        (48, "```oh``` hello ```world``` and then ```some```##"),
        (52, "```oh``` hello ```world``` and then ```somethin```##"),
        (53, "```oh``` hello ```world``` and then ```something```##"),
        (54, "```oh``` hello ```world``` and then ```something```##"),
        (111, "```oh``` hello ```world``` and then ```something```##"),
    ])
def test_trim_markdown(max_length: int, expected_output: str):
    text = "```oh``` hello ```world``` and then ```something```"
    trimmed = Transformer.trim_markdown(text, max_length, "##")
    assert trimmed == expected_output
    assert len(trimmed) <= max_length


@pytest.mark.parametrize(
    "max_length,expected_output", [
        (0, ""),
        (1, "$"),
        (2, "$$"),
        (3, "$$$"),
        (4, "N$$$"),
        (5, "No$$$"),
        (10, "No code$$$"),
        (38, "No code blocks whatsoever in this t$$$"),
        (39, "No code blocks whatsoever in this te$$$"),
        (40, "No code blocks whatsoever in this tex$$$"),
        (41, "No code blocks whatsoever in this text"),
        (42, "No code blocks whatsoever in this text"),
        (111, "No code blocks whatsoever in this text"),
    ]
)
def test_trim_markdown_no_code_blocks(max_length: int, expected_output: str):
    text = "No code blocks whatsoever in this text"
    trimmed = trim_markdown(text, max_length, "$$$")
    assert trimmed == expected_output
    assert len(trimmed) <= max_length
