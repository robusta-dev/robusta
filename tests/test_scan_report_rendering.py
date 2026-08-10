"""
Tests for Transformer.scanReportBlock_to_fileblock() — the conversion of KRR/Popeye
scan results into a report file attached to chat/email sinks.

These tests pin the current PDF-based behavior (fpdf2). If the report format is ever
changed (e.g. different PDF library or HTML output), the format-specific assertions
here are the only ones that should need updating.
"""
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
    text_parts = []
    for stream in re.findall(rb"stream\r?\n(.*?)endstream", pdf_bytes, re.DOTALL):
        try:
            data = zlib.decompress(stream.strip(b"\r\n"))
        except zlib.error:
            data = stream
        for match in re.findall(rb"\(((?:\\.|[^\\()])*)\)\s*Tj", data):
            unescaped = (
                match.replace(b"\\(", b"(").replace(b"\\)", b")").replace(b"\\\\", b"\\")
            )
            text_parts.append(unescaped.decode("latin-1"))
    return "".join(text_parts)


def assert_valid_pdf(contents: bytes):
    assert contents[:5] == b"%PDF-", "report file does not start with the PDF magic bytes"
    assert b"%%EOF" in contents[-32:], "report file does not end with a PDF EOF marker"
    assert len(contents) > 500, "report file is suspiciously small"


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
