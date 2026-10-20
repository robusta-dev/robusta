"""
Minimal SVG chart rendering for Robusta graphs (XY time series, grouped bars, treemap).

Charts are written as plain SVG text and rasterized to PNG by resvg (see
robusta.core.reporting.utils.convert_svg_to_png) for sinks that cannot display SVG.

The layout deliberately reproduces the charts Robusta has always sent (previously drawn with
pygal) so notifications look the same after the switch:
- text sizes are estimated as 0.6 * font size per character (monospace font)
- the plot area is inset by 1/52 of its size on every side
- series lines are 1px wide with 0.8 stroke opacity; fills use 0.6 opacity
- X ticks on time axes are multiples of a power of ten seconds (see _scale_ticks)
"""
import colorsys
import math
from typing import Callable, List, Optional, Sequence, Tuple
from xml.sax.saxutils import escape

# resvg does exact font-family matching with no generic-family fallback, so this must be a font
# installed in the runner image (fonts-dejavu-core); otherwise every text element is dropped.
FONT_FAMILY = "DejaVu Sans Mono"
TITLE_FONT_SIZE = 16
LEGEND_FONT_SIZE = 14
LABEL_FONT_SIZE = 10

FOREGROUND_COLOR = "#607D8B"
GUIDE_COLOR = "#E7EBEB"
BACKGROUND_COLOR = "#FFFFFF"
# the time-series charts use darker text than the bar/treemap charts
TIME_SERIES_TITLE_COLOR = "#11383A"
TIME_SERIES_TEXT_COLOR = "#3f3f3f"

FILL_OPACITY = 0.6
STROKE_OPACITY = 0.8
PLOT_INSET = 1 / 52


class ChartStyle:
    def __init__(self, colors: Sequence[str]):
        self.colors = tuple(colors)


def text_width(text_length: int, font_size: float) -> float:
    return text_length * 0.6 * font_size


def truncate(text: str, max_length: int) -> str:
    if max_length <= 0 or len(text) <= max_length:
        return text
    return text[: max_length - 1] + "…"


def split_title(title: str, width: float) -> List[str]:
    """Wrap a title to the chart width, breaking at the last space that fits (or mid-word if none)."""
    if not title:
        return []
    max_chars = max(int(width / (0.6 * TITLE_FONT_SIZE * 1.1)), 1)
    lines = []
    for line in title.split("\n"):
        while len(line) > max_chars:
            cut = line[:max_chars].rfind(" ")
            if cut <= 0:
                cut = max_chars
            lines.append(line[:cut])
            line = line[cut:].strip()
        lines.append(line)
    return lines


def _darken(hex_color: str, percent: float) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))
    hue, lightness, saturation = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb(hue, max(0.0, lightness - percent / 100), saturation)
    return "#%02x%02x%02x" % tuple(round(v * 255) for v in (r, g, b))


def series_colors(colors: Sequence[str], count: int) -> List[str]:
    """Colors for `count` series. When the palette runs out it is repeated, darker on each cycle."""
    if not colors:
        colors = [FOREGROUND_COLOR]
    if len(colors) >= count:
        return list(colors[:count])
    cycles = 1 + (count - len(colors)) // len(colors)
    result: List[str] = []
    cycle = 0
    while len(result) < count:
        for color in colors:
            result.append(_darken(color, 33 * cycle / cycles) if cycle else color)
            if len(result) >= count:
                break
        cycle += 1
    return result


def _scale_ticks(min_value: float, max_value: float, min_count: int = 4, max_count: int = 16) -> List[float]:
    """
    Evenly spaced ticks at multiples of the largest power of ten that still yields at least
    `min_count` ticks, doubled until there are at most `max_count`.
    On epoch-second axes this gives e.g. a 1000s step, hence labels like 13:00, 13:16, 13:33.
    """
    span = max_value - min_value
    if span <= 0:
        return [min_value]
    order = round(math.log10(max(abs(min_value), abs(max_value)))) - 1
    while span / 10**order < min_count:
        order -= 1
    step = float(10**order)
    while span / step > max_count:
        step *= 2
    first = math.ceil(min_value / step) * step
    ticks = []
    tick = first
    while tick <= max_value + step * 1e-9:
        ticks.append(round(tick, 12) + 0.0)  # + 0.0 turns -0.0 into 0.0
        tick += step
    return ticks


class _Svg:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.parts: List[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" font-family="{FONT_FAMILY}">',
            f'<rect width="{width}" height="{height}" fill="{BACKGROUND_COLOR}"/>',
        ]

    def text(self, x, y, value: str, size: int, fill: str, anchor: str = "start", rotate: float = 0, css_class=""):
        transform = f' transform="rotate({rotate:g} {x:.2f} {y:.2f})"' if rotate else ""
        class_attr = f' class="{css_class}"' if css_class else ""
        self.parts.append(
            f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}"'
            f"{transform}{class_attr}>{escape(value)}</text>"
        )

    def line(self, x1, y1, x2, y2, color: str):
        self.parts.append(f'<path d="M{x1:.2f} {y1:.2f} L{x2:.2f} {y2:.2f}" stroke="{color}" stroke-width="1"/>')

    def rect(self, x, y, width, height, color: str):
        self.parts.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{max(width, 0):.2f}" height="{max(height, 0):.2f}" '
            f'fill="{color}" fill-opacity="{FILL_OPACITY}" stroke="{color}" stroke-opacity="{STROKE_OPACITY}"/>'
        )

    def polyline(self, points: List[Tuple[float, float]], color: str, dasharray: Optional[str]):
        path = "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in points)
        # dashed series get round caps/joins; plain reference lines (limit, request) keep square ends
        dash = (
            f' stroke-dasharray="{escape(dasharray)}" stroke-linejoin="round" stroke-linecap="round"'
            if dasharray
            else ""
        )
        self.parts.append(
            f'<path d="{path}" fill="none" stroke="{color}" stroke-opacity="{STROKE_OPACITY}" stroke-width="1"{dash}/>'
        )

    def group(self, css_class: str):
        self.parts.append(f'<g class="{css_class}">')

    def end_group(self):
        self.parts.append("</g>")

    def render(self) -> bytes:
        return ("\n".join(self.parts) + "\n</svg>").encode("utf-8")


class _Chart:
    title_color = FOREGROUND_COLOR
    text_color = FOREGROUND_COLOR

    def __init__(self, style: ChartStyle, title: str, width: int, height: int, margin_top: float, spacing: float):
        self.style = style
        self.title = title
        self.width = width
        self.height = height
        self.margin_top = margin_top
        self.spacing = spacing

    def _draw_title(self, svg: _Svg):
        for i, line in enumerate(split_title(self.title, self.width), 1):
            svg.text(
                self.width / 2,
                i * (TITLE_FONT_SIZE + self.spacing),
                line,
                TITLE_FONT_SIZE,
                self.title_color,
                "middle",
                css_class="title",
            )

    def _plot_top(self) -> float:
        return self.margin_top + len(split_title(self.title, self.width)) * (TITLE_FONT_SIZE + self.spacing)

    def _draw_no_data(self, svg: _Svg):
        svg.text(self.width / 2, self.height / 2, "No data", 64, FOREGROUND_COLOR, "middle")

    def _draw_side_legend(self, svg: _Svg, titles: List[str], colors: List[str], top: float) -> None:
        box = 12
        svg.group("legends")
        for i, (title, color) in enumerate(zip(titles, colors)):
            y = top + i * LEGEND_FONT_SIZE * 1.5
            svg.rect(self.spacing, y + (LEGEND_FONT_SIZE - box) / 2, box, box, color)
            svg.text(self.spacing + box + 5, y + LEGEND_FONT_SIZE * 0.8, title, LEGEND_FONT_SIZE, self.text_color)
        svg.end_group()

    def _side_legend_width(self, titles: List[str]) -> float:
        if not titles:
            return 0
        return self.spacing + text_width(max(len(t) for t in titles), LEGEND_FONT_SIZE) + 12


class XYChart(_Chart):
    """Line chart over a numeric (usually epoch-seconds) X axis, with the legend below the plot."""

    title_color = TIME_SERIES_TITLE_COLOR
    text_color = TIME_SERIES_TEXT_COLOR

    def __init__(
        self,
        style: ChartStyle,
        title: str = "",
        width: int = 1280,
        height: int = 500,
        show_legend: bool = True,
        value_formatter: Callable[[float], str] = str,
        x_value_formatter: Callable[[float], str] = str,
        x_label_rotation: float = 35,
        legend_columns: int = 5,
        truncate_legend: int = 15,
    ):
        super().__init__(style, title, width, height, margin_top=10, spacing=20)
        self.margin = 20
        self.margin_bottom = 50
        self.show_legend = show_legend
        self.value_formatter = value_formatter
        self.x_value_formatter = x_value_formatter
        self.x_label_rotation = x_label_rotation
        self.legend_columns = legend_columns
        self.truncate_legend = truncate_legend
        self.range: Optional[Tuple[float, float]] = None
        self.y_labels: List[float] = []
        self.series: List[Tuple[str, List[Tuple[float, float]], Optional[str]]] = []

    def add(self, title: str, points: List[Tuple[float, float]], dasharray: Optional[str] = None):
        self.series.append((title, points, dasharray))

    def render(self) -> bytes:
        svg = _Svg(self.width, self.height)
        self._draw_title(svg)
        points = [p for _, series_points, _ in self.series for p in series_points]
        if not points:
            self._draw_no_data(svg)
            return svg.render()

        x_min, x_max = min(p[0] for p in points), max(p[0] for p in points)
        y_min, y_max = self.range if self.range else (min(p[1] for p in points), max(p[1] for p in points))
        if self.y_labels:  # the axis always stretches to fit every label
            y_min, y_max = min(y_min, min(self.y_labels)), max(y_max, max(self.y_labels))
        if y_max == y_min:
            y_max = y_min + 1
        x_ticks = _scale_ticks(x_min, x_max) if x_max > x_min else [x_min]
        x_tick_labels = [self.x_value_formatter(t) for t in x_ticks]
        y_tick_labels = [self.value_formatter(v) for v in self.y_labels]

        # margins
        rotation = math.radians(self.x_label_rotation)
        x_label_width = text_width(max(len(s) for s in x_tick_labels), LABEL_FONT_SIZE)
        x_labels_height = self.spacing + max(x_label_width * abs(math.sin(rotation)), LABEL_FONT_SIZE)
        left = self.margin
        if y_tick_labels:
            left += self.spacing + max(text_width(max(len(s) for s in y_tick_labels), LABEL_FONT_SIZE), LABEL_FONT_SIZE)
        right = self.width - self.margin
        if self.x_label_rotation and self.x_label_rotation % 180 < 90:
            right = self.width - max(x_label_width * abs(math.cos(rotation)), self.margin)
        top = self._plot_top()
        bottom_margin = self.margin_bottom + x_labels_height
        if self.show_legend:
            # the legend's space is sized from floor(series / columns), not the real row count: it matches the
            # previous charts' layout (e.g. 5 series reserve one row more than 4 series do)
            rows_term = len(self.series) // self.legend_columns - 1
            bottom_margin += self.spacing + LEGEND_FONT_SIZE * rows_term * 1.5 + LEGEND_FONT_SIZE
        bottom = self.height - bottom_margin
        plot_width, plot_height = right - left, bottom - top

        def to_x(value: float) -> float:
            if x_max == x_min:
                return left + plot_width / 2
            inner = plot_width * (1 - 2 * PLOT_INSET)
            return left + plot_width * PLOT_INSET + (value - x_min) / (x_max - x_min) * inner

        def to_y(value: float) -> float:
            inner = plot_height * (1 - 2 * PLOT_INSET)
            return top + plot_height * PLOT_INSET + (1 - (value - y_min) / (y_max - y_min)) * inner

        # axes and guides
        svg.group("axis y")
        for value, label in zip(self.y_labels, y_tick_labels):
            y = to_y(value)
            svg.line(left, y, right, y, FOREGROUND_COLOR if value == y_min else GUIDE_COLOR)
            svg.text(left - 5, y + LABEL_FONT_SIZE * 0.35, label, LABEL_FONT_SIZE, self.text_color, "end")
        svg.end_group()
        svg.group("axis x")
        svg.line(left, top, left, bottom, FOREGROUND_COLOR)
        for tick, label in zip(x_ticks, x_tick_labels):
            x = to_x(tick)
            svg.line(x, top, x, bottom, GUIDE_COLOR)
            label_y = bottom + LABEL_FONT_SIZE * 1.5
            svg.text(x, label_y, label, LABEL_FONT_SIZE, self.text_color, "middle", rotate=self.x_label_rotation)
        svg.end_group()

        colors = series_colors(self.style.colors, len(self.series))
        for (_, series_points, dasharray), color in zip(self.series, colors):
            if series_points:
                svg.polyline([(to_x(x), to_y(y)) for x, y in series_points], color, dasharray)

        if self.show_legend:
            box = 8
            column_width = plot_width / self.legend_columns
            legend_top = bottom + x_labels_height + self.spacing
            svg.group("legends")
            for i, ((title, _, _), color) in enumerate(zip(self.series, colors)):
                row, column = divmod(i, self.legend_columns)
                x = left + self.spacing + column * column_width
                y = legend_top + row * LEGEND_FONT_SIZE * 1.5
                svg.rect(x, y + (LEGEND_FONT_SIZE - box) / 2, box, box, color)
                svg.text(
                    x + box + 5,
                    y + LEGEND_FONT_SIZE * 0.8,
                    truncate(title, self.truncate_legend),
                    LEGEND_FONT_SIZE,
                    self.text_color,
                )
            svg.end_group()
        return svg.render()


class BarChart(_Chart):
    """Grouped vertical bars: one group per x label, one bar per series. Legend on the left."""

    def __init__(
        self,
        style: ChartStyle,
        title: str = "",
        x_labels: Optional[List[str]] = None,
        x_label_rotation: float = 0,
        value_formatter: Callable[[float], str] = str,
        width: int = 800,
        height: int = 600,
    ):
        super().__init__(style, title, width, height, margin_top=20, spacing=10)
        self.margin = 20
        self.x_labels = x_labels or []
        self.x_label_rotation = x_label_rotation
        self.value_formatter = value_formatter
        self.series: List[Tuple[str, List[float]]] = []

    def add(self, title: str, values: List[float]):
        self.series.append((title, list(values)))

    def render(self) -> bytes:
        svg = _Svg(self.width, self.height)
        self._draw_title(svg)
        values = [v for _, series_values in self.series for v in series_values]
        if not values or not self.x_labels:
            self._draw_no_data(svg)
            return svg.render()

        y_min, y_max = min(min(values), 0), max(max(values), 0)
        if y_max == y_min:
            y_max = y_min + 1
        y_ticks = _scale_ticks(y_min, y_max)
        y_tick_labels = [self.value_formatter(v) for v in y_ticks]
        legend_titles = [truncate(title, 15) for title, _ in self.series]

        rotation = math.radians(self.x_label_rotation)
        x_label_width = text_width(max(len(s) for s in self.x_labels), LABEL_FONT_SIZE)
        left = self.margin + self._side_legend_width(legend_titles)
        left += self.spacing + max(text_width(max(len(s) for s in y_tick_labels), LABEL_FONT_SIZE), LABEL_FONT_SIZE)
        right = self.width - self.margin
        if self.x_label_rotation and self.x_label_rotation % 180 < 90:
            right = self.width - max(x_label_width * abs(math.cos(rotation)), self.margin)
        top = self._plot_top()
        bottom = (
            self.height - self.margin - self.spacing - max(x_label_width * abs(math.sin(rotation)), LABEL_FONT_SIZE)
        )
        plot_width, plot_height = right - left, bottom - top

        def to_y(value: float) -> float:
            inner = plot_height * (1 - 2 * PLOT_INSET)
            return top + plot_height * PLOT_INSET + (1 - (value - y_min) / (y_max - y_min)) * inner

        svg.group("axis y")
        svg.line(left, top, left, bottom, FOREGROUND_COLOR)
        for value, label in zip(y_ticks, y_tick_labels):
            y = to_y(value)
            svg.line(left, y, right, y, FOREGROUND_COLOR if value == 0 else GUIDE_COLOR)
            svg.text(left - 5, y + LABEL_FONT_SIZE * 0.35, label, LABEL_FONT_SIZE, self.text_color, "end")
        svg.end_group()

        group_width = plot_width * (1 - 2 * PLOT_INSET) / len(self.x_labels)
        groups_left = left + plot_width * PLOT_INSET
        svg.group("axis x")
        for i, label in enumerate(self.x_labels):
            x = groups_left + group_width * (i + 0.5)
            svg.text(
                x,
                bottom + LABEL_FONT_SIZE * 1.5,
                label,
                LABEL_FONT_SIZE,
                self.text_color,
                "middle",
                rotate=self.x_label_rotation % 360,
            )
        svg.end_group()

        # 6% margin around each group, then 6% margin around each bar inside it
        colors = series_colors(self.style.colors, len(self.series))
        group_margin = group_width * 0.06
        bar_slot = (group_width - 2 * group_margin) / len(self.series)
        bar_margin = bar_slot * 0.06
        zero = to_y(0)
        for series_index, ((_, series_values), color) in enumerate(zip(self.series, colors)):
            for i, value in enumerate(series_values):
                x = groups_left + group_width * i + group_margin + series_index * bar_slot + bar_margin
                y = to_y(value)
                svg.rect(x, min(y, zero), bar_slot - 2 * bar_margin, abs(zero - y), color)

        self._draw_side_legend(svg, legend_titles, colors, top + self.spacing)
        return svg.render()


class TreemapChart(_Chart):
    """Areas proportional to each series' value. Legend on the left."""

    def __init__(self, style: ChartStyle, title: str = "", width: int = 800, height: int = 600):
        super().__init__(style, title, width, height, margin_top=20, spacing=10)
        self.margin = 20
        self.series: List[Tuple[str, float]] = []

    def add(self, title: str, value: float):
        self.series.append((title, value))

    @staticmethod
    def _layout(items: List[Tuple[int, float]], x: float, y: float, w: float, h: float, out: List):
        """Split the items in two (in order) where the running total reaches half, and divide the
        rectangle between the halves along its longer side; recurse until one item is left."""
        total = sum(value for _, value in items)
        if total == 0 or not items:
            return
        if len(items) == 1:
            out.append((items[0][0], x, y, w, h))
            return
        split = 1
        running = 0.0
        for i, (_, value) in enumerate(items):
            if running >= total / 2:
                split = i
                break
            running += value
        first, second = items[:split], items[split:]
        share = sum(value for _, value in first) / total
        if h > w:
            TreemapChart._layout(first, x, y, w, share * h, out)
            TreemapChart._layout(second, x, y + share * h, w, h - share * h, out)
        else:
            TreemapChart._layout(first, x, y, share * w, h, out)
            TreemapChart._layout(second, x + share * w, y, w - share * w, h, out)

    def render(self) -> bytes:
        svg = _Svg(self.width, self.height)
        self._draw_title(svg)
        legend_titles = [truncate(title, 15) for title, _ in self.series]
        colors = series_colors(self.style.colors, len(self.series))
        if not self.series or sum(value for _, value in self.series) == 0:
            self._draw_no_data(svg)
            return svg.render()

        left = self.margin + self._side_legend_width(legend_titles)
        top = self._plot_top()
        plot_width = self.width - self.margin - left
        plot_height = self.height - self.margin - top
        inner_left, inner_top = left + plot_width * PLOT_INSET, top + plot_height * PLOT_INSET
        inner_width, inner_height = plot_width * (1 - 2 * PLOT_INSET), plot_height * (1 - 2 * PLOT_INSET)
        rects: List = []
        self._layout(list(enumerate(value for _, value in self.series)), 0, 0, inner_width, inner_height, rects)
        for index, x, y, w, h in rects:
            # the layout's y grows upwards from the bottom of the plot, as the charts always have
            svg.rect(inner_left + x, inner_top + inner_height - y - h, w, h, colors[index])

        self._draw_side_legend(svg, legend_titles, colors, top + self.spacing)
        return svg.render()
