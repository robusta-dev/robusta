"""
Tests for the SVG -> raster-image conversion used by chat sinks.

Robusta renders Prometheus/resource graphs as pygal SVG charts and rasterizes them
before sending to chat platforms that cannot display SVG:
- convert_svg_to_png / add_pngs_for_all_svgs (Slack, Discord, Mattermost, RocketChat,
  Jira, Webex, Telegram, Pushover, Zulip, Yandex)
- MsTeamsAdaptiveCardFilesImage (MS Teams needs base64 JPEG data-URLs)

These tests pin the current behavior so the rasterizer library can be swapped safely.
"""
from io import BytesIO

import pygal
import pytest
from PIL import Image
from prometrix import PrometheusQueryResult

from robusta.core.model.base_params import ChartValuesFormat
from robusta.core.playbooks.prometheus_enrichment_utils import build_chart_from_prometheus_result
from robusta.core.reporting.blocks import FileBlock, MarkdownBlock
from robusta.core.reporting.utils import add_pngs_for_all_svgs, convert_svg_to_png
from robusta.integrations.msteams.msteams_adaptive_card_files_image import MsTeamsAdaptiveCardFilesImage

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def decode_image(image_bytes: bytes) -> Image.Image:
    image = Image.open(BytesIO(image_bytes))
    image.load()  # force decoding of the full image, not just the header
    return image


def make_prometheus_matrix(series_count: int = 2, points: int = 10) -> dict:
    base_timestamp = 1764072332
    result = []
    for series_idx in range(series_count):
        values = [
            [base_timestamp + point_idx * 60, str(100.0 + 10 * series_idx + point_idx)]
            for point_idx in range(points)
        ]
        result.append(
            {
                "metric": {"pod": f"pod-{series_idx}", "namespace": "default"},
                "values": values,
            }
        )
    return {"resultType": "matrix", "result": result}


@pytest.fixture
def simple_pygal_svg() -> bytes:
    chart = pygal.Line(width=400, height=300)
    chart.title = "simple chart"
    chart.add("series-a", [1, 2, 3, 2, 5])
    chart.add("series-b", [5, 4, 3, 4, 1])
    return chart.render()


@pytest.fixture
def robusta_styled_chart_svg() -> bytes:
    """An SVG built through the real chart pipeline, custom CSS injection included."""
    query_result = PrometheusQueryResult(data=make_prometheus_matrix())
    chart = build_chart_from_prometheus_result(
        query_result,
        chart_title="Memory usage",
        values_format=ChartValuesFormat.Bytes,
    )
    return chart.render()


def test_convert_simple_pygal_svg_to_png(simple_pygal_svg):
    png = convert_svg_to_png(simple_pygal_svg)

    assert png is not None
    assert png[:8] == PNG_MAGIC
    image = decode_image(png)
    assert image.format == "PNG"
    assert image.size == (400, 300)


def test_convert_robusta_styled_chart_to_png(robusta_styled_chart_svg):
    """The chart pipeline injects custom CSS into the pygal SVG; the rasterizer must
    handle it. This is the closest unit-level reproduction of what every
    graph-bearing alert notification goes through on its way to a chat sink."""
    png = convert_svg_to_png(robusta_styled_chart_svg)

    assert png is not None
    assert png[:8] == PNG_MAGIC
    image = decode_image(png)
    assert image.format == "PNG"
    # pygal charts in the alert pipeline are rendered at a fixed 1280x500
    assert image.size == (1280, 500)


def test_invalid_svg_returns_none():
    assert convert_svg_to_png(b"this is not svg at all") is None


def test_add_pngs_for_all_svgs_appends_png_twin(simple_pygal_svg):
    svg_block = FileBlock("chart.svg", simple_pygal_svg)
    text_block = FileBlock("log.txt", b"some log")
    markdown_block = MarkdownBlock("not a file")
    original_blocks = [svg_block, text_block, markdown_block]

    result = add_pngs_for_all_svgs(original_blocks)

    # the input list is not mutated
    assert original_blocks == [svg_block, text_block, markdown_block]

    # output keeps every original block and appends exactly one PNG twin per SVG
    assert result[:3] == [svg_block, text_block, markdown_block]
    assert len(result) == 4
    png_twin = result[3]
    assert isinstance(png_twin, FileBlock)
    assert png_twin.filename == "chart.png"
    assert png_twin.contents[:8] == PNG_MAGIC


def test_add_pngs_for_all_svgs_skips_unconvertible_svg():
    bad_svg_block = FileBlock("broken.svg", b"not really svg")

    result = add_pngs_for_all_svgs([bad_svg_block])

    # conversion failure must not raise and must not add a twin
    assert result == [bad_svg_block]


def test_msteams_svg_becomes_jpeg_data_url(robusta_styled_chart_svg):
    svg_block = FileBlock("graph.svg", robusta_styled_chart_svg)

    image_set = MsTeamsAdaptiveCardFilesImage.create_files_for_presentation([svg_block])

    images = image_set.get_map_value()["images"]
    assert len(images) == 1
    url = images[0]["url"]
    assert url.startswith("data:image/jpeg;base64,")

    import base64

    jpeg_bytes = base64.b64decode(url[len("data:image/jpeg;base64,"):])
    image = decode_image(jpeg_bytes)
    assert image.format == "JPEG"
    assert image.size == (1280, 500)


def test_msteams_png_becomes_jpeg_data_url(simple_pygal_svg):
    png_bytes = convert_svg_to_png(simple_pygal_svg)
    png_block = FileBlock("chart.png", png_bytes)

    image_set = MsTeamsAdaptiveCardFilesImage.create_files_for_presentation([png_block])

    images = image_set.get_map_value()["images"]
    assert len(images) == 1
    url = images[0]["url"]
    assert url.startswith("data:image/jpeg;base64,")

    import base64

    jpeg_bytes = base64.b64decode(url[len("data:image/jpeg;base64,"):])
    image = decode_image(jpeg_bytes)
    assert image.format == "JPEG"


def test_msteams_non_image_files_are_ignored():
    text_block = FileBlock("log.txt", b"some log")

    result = MsTeamsAdaptiveCardFilesImage.create_files_for_presentation([text_block])

    assert result == []
