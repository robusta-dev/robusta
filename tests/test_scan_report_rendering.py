"""
Tests for Transformer.scanReportBlock_to_fileblock() — the conversion of KRR/Popeye
scan results into a report file attached to chat/email sinks.

These tests pin the PDF-based report behavior. If the report format is ever changed
(e.g. different PDF library or HTML output), the format-specific assertions here are
the only ones that should need updating.
"""
import base64
import re
import zlib
from datetime import datetime

import pytest

from robusta.core.reporting.blocks import (
    FileBlock,
    KRRScanReportBlock,
    MarkdownBlock,
    PopeyeScanReportBlock,
    ScanReportRow,
)
from robusta.core.reporting.consts import ScanType
from robusta.core.sinks.transformer import Transformer

START_TIME = datetime(2024, 5, 1, 10, 0, 0)
END_TIME = datetime(2024, 5, 1, 10, 5, 0)


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text drawn with core fonts from a PDF, without external PDF libraries.

    Decompresses every content stream and collects the literal strings of Tj/TJ
    text-showing operators. Good enough for PDFs produced with built-in (core)
    fonts, which is what the scan report uses.
    """
    def decode_stream(stream: bytes) -> bytes:
        stream = stream.strip(b"\r\n")
        for decoder in (
            zlib.decompress,  # FlateDecode
            lambda raw: zlib.decompress(base64.a85decode(raw, adobe=True)),  # ASCII85Decode + FlateDecode
            lambda raw: raw,  # uncompressed
        ):
            try:
                return decoder(stream)
            except Exception:
                continue
        return stream

    escape_map = {b"n": 10, b"r": 13, b"t": 9, b"b": 8, b"f": 12, b"(": 40, b")": 41, b"\\": 92}

    def unescape_pdf_string(raw: bytes) -> bytes:
        out = bytearray()
        i = 0
        while i < len(raw):
            if raw[i : i + 1] != b"\\":
                out.append(raw[i])
                i += 1
                continue
            next_char = raw[i + 1 : i + 2]
            if next_char in escape_map:
                out.append(escape_map[next_char])
                i += 2
            elif next_char.isdigit():  # octal escape, up to 3 digits
                digits_end = i + 2
                while digits_end < len(raw) and digits_end < i + 4 and raw[digits_end : digits_end + 1].isdigit():
                    digits_end += 1
                out.append(int(raw[i + 1 : digits_end], 8) & 0xFF)
                i = digits_end
            else:
                i += 1  # stray backslash
        return bytes(out)

    text_parts = []
    for stream in re.findall(rb"stream\r?\n(.*?)endstream", pdf_bytes, re.DOTALL):
        data = decode_stream(stream)
        for match in re.findall(rb"\(((?:\\.|[^\\()])*)\)\s*Tj", data):
            text_parts.append(unescape_pdf_string(match).decode("latin-1"))
    return "".join(text_parts)


def assert_valid_pdf(contents: bytes):
    assert contents[:5] == b"%PDF-", "report file does not start with the PDF magic bytes"
    assert b"%%EOF" in contents[-32:], "report file does not end with a PDF EOF marker"
    assert len(contents) > 500, "report file is suspiciously small"


def count_pdf_pages(pdf_bytes: bytes) -> int:
    # page objects are declared as "/Type /Page"; the negative lookahead excludes
    # the "/Type /Pages" page-tree object
    return len(re.findall(rb"/Type\s*/Page(?!s)", pdf_bytes))


def make_krr_row(kind: str, name: str, namespace: str, container: str, priority: float) -> ScanReportRow:
    return ScanReportRow(
        scan_id="8481dd4a-1234-4444-9999-b8c1d915e7a1",
        scan_type=ScanType.KRR,
        kind=kind,
        name=name,
        namespace=namespace,
        container=container,
        priority=priority,
        content=[
            {
                "resource": "cpu",
                "allocated": {"request": 0.1, "limit": 0.5},
                "recommended": {"request": 0.25, "limit": None},
                "info": "avg usage",
            },
            {
                "resource": "memory",
                "allocated": {"request": 134217728.0, "limit": 268435456.0},
                "recommended": {"request": 67108864.0, "limit": 134217728.0},
                "info": None,
            },
        ],
    )


def make_popeye_row(
    kind: str, name: str, namespace: str, priority: float, messages=None
) -> ScanReportRow:
    messages = messages if messages is not None else [{"level": 2, "message": "default message"}]
    return ScanReportRow(
        scan_id="16a9b567-1234-4444-9999-b8c1d915e7a2",
        scan_type=ScanType.POPEYE,
        kind=kind,
        name=name,
        namespace=namespace,
        container="",
        priority=priority,
        content=messages,
    )


@pytest.fixture
def krr_block() -> KRRScanReportBlock:
    return KRRScanReportBlock(
        title="KRR scan",
        scan_id="8481dd4a-1234-4444-9999-b8c1d915e7a1",
        type=ScanType.KRR,
        start_time=START_TIME,
        end_time=END_TIME,
        score="85",
        config="{'cpu_percentile': 99}",
        results=[
            make_krr_row("Deployment", "checkout-service", "prod", "server", 1.0),
            make_krr_row("Deployment", "payments-api", "prod", "api", 3.0),
            make_krr_row("DaemonSet", "node-agent", "kube-system", "agent", 2.0),
        ],
    )


@pytest.fixture
def popeye_block() -> PopeyeScanReportBlock:
    return PopeyeScanReportBlock(
        title="Popeye scan",
        scan_id="16a9b567-1234-4444-9999-b8c1d915e7a2",
        type=ScanType.POPEYE,
        start_time=START_TIME,
        end_time=END_TIME,
        score="72",
        config="popeye config here",
        results=[
            make_popeye_row(
                "pods", "checkout-service-b578f79f4-2rzm8", "prod", 3,
                messages=[{"level": 3, "message": "container is running as root"}],
            ),
            make_popeye_row(
                "services", "checkout-service", "prod", 1,
                messages=[{"level": 1, "message": "no liveness probe"}],
            ),
        ],
    )


def test_krr_scan_report_to_file(krr_block):
    result = Transformer.scanReportBlock_to_fileblock(krr_block)

    assert isinstance(result, FileBlock)
    assert result.filename == "Krr report.pdf"
    assert_valid_pdf(result.contents)

    text = extract_pdf_text(result.contents)
    assert "Krr report" in text
    assert "85" in text  # score
    assert "B" in text  # grade for score 85
    # every resource from every section must appear in the report
    for name in ("checkout-service", "payments-api", "node-agent"):
        assert name in text, f"resource {name} missing from report"
    for namespace in ("prod", "kube-system"):
        assert namespace in text, f"namespace {namespace} missing from report"
    # section headers are the resource kinds
    for kind in ("Deployment", "DaemonSet"):
        assert kind in text, f"section {kind} missing from report"
    # config section is included
    assert "cpu_percentile" in text


def test_popeye_scan_report_to_file(popeye_block):
    result = Transformer.scanReportBlock_to_fileblock(popeye_block)

    assert isinstance(result, FileBlock)
    assert result.filename == "Popeye report.pdf"
    assert_valid_pdf(result.contents)

    text = extract_pdf_text(result.contents)
    assert "Popeye report" in text
    assert "72" in text  # score
    assert "C" in text  # grade for score 72
    assert "checkout-service-b578f79f4-2rzm8" in text
    assert "container is running as root" in text
    assert "no liveness probe" in text
    for kind in ("pods", "services"):
        assert kind in text, f"section {kind} missing from report"


def test_non_scan_blocks_pass_through_unchanged():
    markdown = MarkdownBlock("hello")
    file_block = FileBlock("log.txt", b"contents")

    assert Transformer.scanReportBlock_to_fileblock(markdown) is markdown
    assert Transformer.scanReportBlock_to_fileblock(file_block) is file_block


def test_empty_scan_results_still_produce_valid_report(krr_block):
    krr_block.results = []

    result = Transformer.scanReportBlock_to_fileblock(krr_block)

    assert isinstance(result, FileBlock)
    assert result.filename == "Krr report.pdf"
    assert_valid_pdf(result.contents)
    text = extract_pdf_text(result.contents)
    assert "Krr report" in text


@pytest.mark.parametrize("bad_score", ["85.5", "N/A", "", None])
def test_non_integer_score_skips_badge_without_breaking_report(popeye_block, bad_score):
    popeye_block.score = bad_score

    result = Transformer.scanReportBlock_to_fileblock(popeye_block)

    assert isinstance(result, FileBlock)
    assert_valid_pdf(result.contents)
    text = extract_pdf_text(result.contents)
    assert "Popeye report" in text  # report still renders, just without the score badge
    if bad_score:  # "85.5", "N/A"
        assert bad_score not in text, "score badge should have been skipped"
    elif bad_score is None:
        assert "None" not in text, "score badge should have been skipped"
    # for "" there is no score text whose absence could be asserted


def test_row_taller_than_page_splits_across_pages(popeye_block):
    popeye_block.results = [
        make_popeye_row(
            "pods", "noisy-pod", "prod", 3,
            messages=[{"level": 2, "message": f"issue number {i} with some detail text"} for i in range(200)],
        ),
    ]

    result = Transformer.scanReportBlock_to_fileblock(popeye_block)

    assert isinstance(result, FileBlock)
    assert_valid_pdf(result.contents)
    assert count_pdf_pages(result.contents) > 1, "a 200-issue row should span multiple pages"
    text = extract_pdf_text(result.contents)
    for i in range(200):
        assert f"issue number {i} with some detail text" in text, f"issue {i} missing from the report"


def test_hostile_cell_content_does_not_break_report(popeye_block):
    popeye_block.config = "config with (parens), backslash \\ and percent 100%"
    popeye_block.results = [
        make_popeye_row(
            "pods", "name-with-(parens)", "ns-with-\\backslash", 3,
            messages=[
                {"level": 3, "message": "message with (unbalanced paren"},
                {"level": 2, "message": "**markdown bold** and _underscores_"},
                {"level": 1, "message": "latin-1 accents: café naïve"},
                {"level": 2, "message": "long message " + "word " * 150},
            ],
        ),
    ]

    result = Transformer.scanReportBlock_to_fileblock(popeye_block)

    assert isinstance(result, FileBlock)
    assert_valid_pdf(result.contents)
    text = extract_pdf_text(result.contents)
    assert "name-with-(parens)" in text
    assert "message with (unbalanced paren" in text
    assert "café naïve" in text
