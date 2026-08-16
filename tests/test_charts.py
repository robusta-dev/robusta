"""
Tests for the matplotlib-backed chart renderers that produce Robusta's
Prometheus/resource graphs.

These cover the contract the rest of the pipeline depends on: SVG bytes out, at
an exact pixel size, rasterizable by resvg, with Robusta's styling applied.
"""
import warnings
from io import BytesIO

import pytest
from PIL import Image

from robusta.core.reporting.charts import BarChart, ChartStyle, TreemapChart, XYChart, _truncate, squarify
from robusta.core.reporting.custom_rendering import charts_style
from robusta.core.reporting.utils import convert_svg_to_png

SVG_ROOT = b"<svg"


def png_size(svg: bytes):
    png = convert_svg_to_png(svg)
    assert png is not None, "SVG failed to rasterize"
    image = Image.open(BytesIO(png))
    image.load()
    return image.size


def line_chart(**kwargs) -> XYChart:
    chart = XYChart(**kwargs)
    chart.title = "test chart"
    chart.add("series-a", [(0, 1.0), (1, 2.0), (2, 3.0)])
    return chart


# --- XY chart -------------------------------------------------------------------


def test_xy_chart_renders_svg():
    svg = line_chart().render()

    assert SVG_ROOT in svg[:512]
    assert svg.rstrip().endswith(b"</svg>")


@pytest.mark.parametrize("width,height", [(1280, 500), (400, 300), (800, 600)])
def test_xy_chart_rasterizes_at_exact_requested_size(width, height):
    """matplotlib emits points, not pixels; the renderer pins the root <svg> to an
    exact pixel size so sinks get a predictable raster."""
    svg = line_chart(width=width, height=height).render()

    assert png_size(svg) == (width, height)


def test_render_is_deterministic():
    """Identical input must produce identical bytes - no embedded timestamp."""
    assert line_chart().render() == line_chart().render()


def test_value_formatter_applied_to_y_axis():
    """Y-axis ticks are labelled through value_formatter (Bytes, CPUUsage, ...).

    Glyphs are emitted as paths, so the formatter itself is spied on rather than
    the rendered text.
    """
    seen = []
    chart = line_chart()
    chart.range = (0, 100)
    chart.y_labels = [0, 50, 100]
    chart.value_formatter = lambda v: seen.append(v) or f"{v} pct"

    chart.render()

    assert seen == [0, 50, 100]


def test_hidden_legend_is_not_rendered():
    with_legend = line_chart(show_legend=True).render()
    without_legend = line_chart(show_legend=False).render()

    assert len(without_legend) < len(with_legend)


def test_dashed_series_renders():
    """stroke_style dasharray must survive translation into matplotlib dashes."""
    chart = XYChart()
    chart.add(
        "dashed",
        [(0, 1.0), (1, 2.0)],
        stroke_style={"width": 8, "dasharray": "8", "linecap": "round"},
        show_dots=False,
    )

    assert png_size(chart.render()) == (1280, 500)


def test_empty_chart_still_renders():
    """A query returning no series must not blow up the enrichment."""
    chart = XYChart()
    chart.title = "no data"
    chart.y_labels = []
    chart.show_minor_y_labels = False

    assert png_size(chart.render()) == (1280, 500)


def test_empty_chart_draws_no_x_ticks():
    """With no series there is no real x-range, so the placeholder range must not
    get labelled - it would render every tick as the epoch."""
    formatted = []
    chart = XYChart()
    chart.x_value_formatter = lambda t: formatted.append(t) or "tick"

    chart.render()

    assert formatted == []


def test_single_point_is_visible_even_with_dots_disabled():
    """The alert pipeline builds every series with show_dots=False. One sample has
    no segment to draw, so without a marker the chart would come out blank."""
    chart = XYChart()
    chart.add("solo", [(1755300000, 42.0)], show_dots=False)

    png = convert_svg_to_png(chart.render())
    image = Image.open(BytesIO(png)).convert("RGB")
    colors = {c for _, c in (image.getcolors(maxcolors=1_000_000) or [])}
    # the default first palette colour is #9747FF - some trace of it must survive
    assert any(r > 100 and b > 180 and g < 120 for r, g, b in colors), "the lone sample was not drawn"


def test_all_zero_series_does_not_warn_about_singular_axis():
    """A metric flat at zero collapses the callers' derived range to (0, 0), which
    is still truthy - the axis must be given height rather than handed to
    matplotlib as a singular transform."""
    chart = XYChart()
    chart.add("quiet", [(0, 0.0), (1, 0.0), (2, 0.0)])
    chart.range = (0, 0.0)
    chart.y_labels = [0, 0, 0, 0, 0]

    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        svg = chart.render()

    assert png_size(svg) == (1280, 500)


def test_collapsed_range_collapses_duplicate_y_labels():
    """The same collapse makes every derived tick identical; five stacked zeros
    would be drawn on top of each other."""
    seen = []
    chart = XYChart()
    chart.add("quiet", [(0, 0.0), (1, 0.0)])
    chart.range = (0, 0.0)
    chart.y_labels = [0, 0, 0, 0, 0]
    chart.value_formatter = lambda v: seen.append(v) or str(v)

    chart.render()

    assert seen == [0], "duplicate ticks should collapse to a single label"


def test_distinct_y_labels_are_left_alone():
    seen = []
    chart = line_chart()
    chart.range = (0, 100)
    chart.y_labels = [0, 25, 50, 75, 100]
    chart.value_formatter = lambda v: seen.append(v) or str(v)

    chart.render()

    assert seen == [0, 25, 50, 75, 100]


def test_single_point_does_not_warn_about_singular_axis():
    """One sample gives a zero-width x-range; the limits must be widened rather
    than left for matplotlib to complain about."""
    chart = XYChart()
    chart.add("solo", [(1755300000, 42.0)])

    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        svg = chart.render()

    assert png_size(svg) == (1280, 500)


# --- label truncation -----------------------------------------------------------


def test_truncate_matches_pygal_semantics():
    # limit is inclusive of the ellipsis, as pygal's truncate_legend was
    assert _truncate("checkout-api-7d9f8b6c4-hk2xl", 15) == "checkout-api-7…"
    assert len(_truncate("checkout-api-7d9f8b6c4-hk2xl", 15)) == 15


def test_truncate_leaves_short_labels_alone():
    assert _truncate("short", 15) == "short"


def test_truncate_flattens_multiline_labels():
    """Series labels are built by joining metric values with newlines."""
    assert _truncate("pod-a\nprod", None) == "pod-a prod"


# --- bar chart ------------------------------------------------------------------


def test_bar_chart_renders_with_missing_values():
    """node_cpu_analysis passes a negative sentinel for pods with no request."""
    chart = BarChart(style=charts_style())
    chart.title = "actual vs requested"
    chart.x_labels = ["pod-a", "pod-b", "pod-c"]
    chart.value_formatter = lambda v: f"{v:.2f} vCPU"
    chart.add("Actual CPU Usage", [1.4, 0.2, 0.1])
    chart.add("CPU Request", [1.0, 0.1, -0.001])

    assert png_size(chart.render()) == (800, 600)


# --- treemap --------------------------------------------------------------------


def test_treemap_renders():
    chart = TreemapChart(style=charts_style())
    chart.title = "cpu by pod"
    chart.value_formatter = lambda x: f"{int(x * 100)}%"
    for index, value in enumerate([0.4, 0.25, 0.15, 0.1, 0.1]):
        chart.add(f"pod-{index}", [value])

    assert png_size(chart.render()) == (800, 600)


def test_treemap_ignores_non_positive_values():
    """Free-CPU style entries can legitimately compute to zero or below."""
    chart = TreemapChart()
    chart.add("real", [0.5])
    chart.add("zero", [0])
    chart.add("negative", [-0.2])

    assert png_size(chart.render()) == (800, 600)


def test_treemap_with_no_positive_values_renders_empty():
    chart = TreemapChart()
    chart.title = "nothing to show"
    chart.add("zero", [0])

    assert png_size(chart.render()) == (800, 600)


# --- squarify layout ------------------------------------------------------------

def squarified(values, width=100.0, height=100.0):
    ordered = sorted(values, reverse=True)
    total = sum(ordered)
    normalized = [v * width * height / total for v in ordered]
    return squarify(normalized, 0.0, 0.0, width, height), ordered


def test_squarify_produces_one_rect_per_value():
    rects, ordered = squarified([5, 3, 2, 1, 1])

    assert len(rects) == len(ordered)


def test_squarify_areas_are_proportional_to_values():
    values = [5, 3, 2, 1, 1]
    rects, ordered = squarified(values)

    total = sum(ordered)
    for (_, _, w, h), value in zip(rects, ordered):
        expected_share = value / total
        assert w * h / (100.0 * 100.0) == pytest.approx(expected_share, rel=1e-6)


def test_squarify_rects_stay_inside_the_canvas():
    rects, _ = squarified([5, 3, 2, 1, 1])

    for x, y, w, h in rects:
        assert x >= -1e-9 and y >= -1e-9
        assert x + w <= 100.0 + 1e-6
        assert y + h <= 100.0 + 1e-6


def test_squarify_rects_do_not_overlap():
    rects, _ = squarified([5, 3, 2, 1, 1, 4, 6])

    for i, a in enumerate(rects):
        for b in rects[i + 1:]:
            separated = (
                a[0] + a[2] <= b[0] + 1e-6
                or b[0] + b[2] <= a[0] + 1e-6
                or a[1] + a[3] <= b[1] + 1e-6
                or b[1] + b[3] <= a[1] + 1e-6
            )
            assert separated, f"{a} overlaps {b}"


def test_squarify_tiles_the_whole_canvas():
    rects, _ = squarified([5, 3, 2, 1, 1])

    assert sum(w * h for _, _, w, h in rects) == pytest.approx(100.0 * 100.0, rel=1e-6)


def test_squarify_handles_a_single_value():
    rects, _ = squarified([1])

    assert rects == [(0.0, 0.0, 100.0, 100.0)]


# --- style ----------------------------------------------------------------------


def test_charts_style_uses_supplied_colors():
    style = charts_style(graph_colors=("#111111", "#222222"))

    assert style.colors == ("#111111", "#222222")
    assert style.color_at(0) == "#111111"
    assert style.color_at(2) == "#111111", "palette must cycle"


def test_charts_style_has_a_default_palette():
    assert charts_style().colors[0] == "#9747FF"


def test_chart_style_falls_back_when_palette_is_empty():
    assert ChartStyle(colors=()).color_at(0) == "#9747FF"
