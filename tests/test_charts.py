"""
Tests for robusta.core.reporting.charts, the SVG renderer behind every Robusta graph.

Expected values (tick positions, extended palette colors, layout) were taken from the charts
Robusta produced before this renderer existed, so these tests also guard against visual drift.
"""
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from io import BytesIO

from PIL import Image

from robusta.core.reporting.charts import (
    BarChart,
    ChartStyle,
    TreemapChart,
    XYChart,
    _scale_ticks,
    series_colors,
    split_title,
    truncate,
)
from robusta.core.reporting.custom_rendering import charts_style
from robusta.core.reporting.utils import convert_svg_to_png


def texts(svg: bytes, css_class: str):
    root = ET.fromstring(svg)
    ns = "{http://www.w3.org/2000/svg}"
    for group in root.iter(f"{ns}g"):
        if group.get("class") == css_class:
            return [t.text for t in group.iter(f"{ns}text")]
    return []


def title_lines(svg: bytes):
    root = ET.fromstring(svg)
    return [t.text for t in root.iter("{http://www.w3.org/2000/svg}text") if t.get("class") == "title"]


def rendered_size(svg: bytes):
    return Image.open(BytesIO(convert_svg_to_png(svg))).size


def fmt_utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%H:%M")


def test_scale_ticks_on_epoch_seconds_use_1000s_steps():
    start = datetime(2026, 9, 22, 12, 47, tzinfo=timezone.utc).timestamp()
    end = datetime(2026, 9, 22, 14, 17, tzinfo=timezone.utc).timestamp()
    assert [fmt_utc(t) for t in _scale_ticks(start, end)] == ["13:00", "13:16", "13:33", "13:50", "14:06"]


def test_scale_ticks_on_small_values():
    assert _scale_ticks(-0.001, 0.84) == [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]


def test_scale_ticks_double_the_step_when_too_dense():
    # a step of 10 would give 17 ticks, more than the 16 allowed
    assert _scale_ticks(0, 170) == [0, 20, 40, 60, 80, 100, 120, 140, 160]


def test_series_colors_extend_palette_by_darkening():
    palette = ("#9747FF", "#FF5959", "#0DC291", "#2a0065", "#1e0047")
    assert series_colors(palette, 3) == ["#9747FF", "#FF5959", "#0DC291"]
    assert series_colors(palette, 8)[5:] == ["#45009e", "#b00000", "#02241b"]


def test_truncate_and_split_title():
    assert truncate("payments-processor-01", 15) == "payments-proce…"
    assert truncate("checkout-6b7c9d", 15) == "checkout-6b7c9d"
    long_title = "sum(rate(http_requests_total[5m])) " * 6
    lines = split_title(long_title.strip(), 1280)
    assert len(lines) == 2
    assert all(len(line) <= 121 for line in lines)
    assert " ".join(lines) == long_title.strip()


def test_xy_chart_renders_labels_legend_and_size():
    chart = XYChart(
        charts_style(("#3F3F3F", "#FF5959")), title="Memory <usage> & more", value_formatter=lambda v: f"{v:.0f} MiB"
    )
    chart.range = (0, 600)
    chart.y_labels = [0, 150, 300, 450, 600]
    chart.add("very-long-container-name", [(1_790_000_000 + i * 60, 100 + i) for i in range(60)], dasharray="8")
    chart.add("Limit", [(1_790_000_000, 512), (1_790_000_000 + 59 * 60, 512)])

    svg = chart.render()

    assert title_lines(svg) == ["Memory <usage> & more"]  # escaped in the SVG, intact after parsing
    assert texts(svg, "legends") == ["very-long-cont…", "Limit"]
    assert texts(svg, "axis y") == ["0 MiB", "150 MiB", "300 MiB", "450 MiB", "600 MiB"]
    assert len(texts(svg, "axis x")) >= 4
    assert b'stroke-dasharray="8"' in svg
    assert rendered_size(svg) == (1280, 500)


def test_xy_chart_axis_stretches_to_fit_labels():
    chart = XYChart(charts_style())
    chart.range = (0, 0.6)
    chart.y_labels = [0, 0, 0, 0, 1]
    chart.add("cpu", [(0, 0.5), (100, 0.5)])
    svg = chart.render()
    # on a 0..1 axis the 0.5 line is in the vertical middle of the plot (on 0..0.6 it would be near the top)
    ns = "{http://www.w3.org/2000/svg}"
    x_axis = next(g for g in ET.fromstring(svg).iter(f"{ns}g") if g.get("class") == "axis x")
    plot_top, plot_bottom = map(float, re.match(r"M[\d.]+ ([\d.]+) L[\d.]+ ([\d.]+)", x_axis[0].get("d")).groups())
    (line_y,) = re.findall(rb'<path d="M[\d.]+ ([\d.]+) L[\d.]+ \1" fill="none"', svg)
    assert abs(float(line_y) - (plot_top + plot_bottom) / 2) < 1


def test_xy_chart_without_data_or_legend():
    empty = XYChart(charts_style(), title="nothing")
    assert b"No data" in empty.render()

    chart = XYChart(charts_style(), show_legend=False)
    chart.add("a", [(0, 1), (1, 2)])
    assert texts(chart.render(), "legends") == []


def test_bar_chart():
    chart = BarChart(
        charts_style(),
        title="Actual Vs Requested",
        x_labels=["a-pod", "b-pod"],
        x_label_rotation=-40,
        value_formatter=lambda v: f"{v:.2f} vCPU",
    )
    chart.add("Actual CPU Usage", [0.84, -0.001])
    chart.add("CPU Request", [0.25, 0.5])
    svg = chart.render()
    assert texts(svg, "legends") == ["Actual CPU Usa…", "CPU Request"]
    assert texts(svg, "axis y")[0] == "0.00 vCPU" and texts(svg, "axis y")[-1] == "0.80 vCPU"
    assert texts(svg, "axis x") == ["a-pod", "b-pod"]
    assert rendered_size(svg) == (800, 600)


def test_treemap_areas_are_proportional_and_fill_the_plot():
    values = [0.07, 0.38, 0.21, 0.14, 0.06, 0.09, 0.02, 0.03]
    rects = []
    TreemapChart._layout(list(enumerate(values)), 0, 0, 600, 500, rects)
    assert sorted(r[0] for r in rects) == list(range(len(values)))
    total_area = 600 * 500
    for index, x, y, w, h in rects:
        assert abs(w * h / total_area - values[index] / sum(values)) < 1e-9
        assert 0 <= x and x + w <= 600 + 1e-9 and 0 <= y and y + h <= 500 + 1e-9


def test_treemap_layout_matches_previous_charts():
    # node_cpu_enricher's 800x600 treemap; expected rectangles measured from the charts Robusta sent before
    values = [0.07, 0.38, 0.21, 0.14, 0.06, 0.09, 0.02, 0.03]
    width, height = 612 * 50 / 52, 534 * 50 / 52
    rects = []
    TreemapChart._layout(list(enumerate(values)), 0, 0, width, height, rects)
    by_index = {index: (x, y, w, h) for index, x, y, w, h in rects}
    expected = {
        0: (0, 0, 60.415, 350.087),  # y grows upwards from the bottom of the plot
        1: (60.415, 0, 327.969, 350.087),
        2: (0, 350.087, 388.385, 163.374),
        7: (468.415, 437.952, 120.046, 75.509),
    }
    for index, rect in expected.items():
        assert all(abs(a - b) < 0.01 for a, b in zip(by_index[index], rect)), (index, by_index[index])


def test_treemap_renders():
    chart = TreemapChart(ChartStyle(("#9747FF", "#FF5959")), title="CPU Usage on Node n1")
    chart.add("Non-container usage", 0.1)
    chart.add("Free CPU", 0.4)
    chart.add("pod-a", 0.5)
    svg = chart.render()
    assert texts(svg, "legends") == ["Non-container …", "Free CPU", "pod-a"]
    assert svg.count(b"<rect") == 1 + 3 + 3  # background, 3 areas, 3 legend boxes
    # the first area is laid out from the bottom-left corner of the plot, as in previous charts
    first_area = re.search(rb'<rect x="[\d.]+" y="([\d.]+)" width="[\d.]+" height="([\d.]+)" fill="#9747FF"', svg)
    y, h = map(float, first_area.groups())
    plot_bottom = 600 - 20 - (600 - 20 - 46) / 52
    assert abs(y + h - plot_bottom) < 0.01
    assert rendered_size(svg) == (800, 600)
