"""SVG chart rendering for Robusta enrichments.

Charts are produced as SVG bytes and handed to sinks as FileBlock/GraphBlock
contents; chat sinks that cannot display SVG rasterize them via
``robusta.core.reporting.utils.convert_svg_to_png``.

The classes here expose a small pygal-shaped surface (``add()`` + ``render()``
plus a handful of assignable attributes) because that is the shape the chart
builders and playbooks were written against.

Implementation notes:

- matplotlib is driven through the object-oriented ``Figure``/``FigureCanvasSVG``
  API rather than ``pyplot``. There is no global figure registry to leak and no
  backend to select, which matters in a long-lived server process.
- Text is rendered as paths (matplotlib's default ``svg.fonttype``), so the
  rasterizer does not need any font installed in the container to produce
  correct output.
- The SVG's ``width``/``height`` are rewritten to exact pixel values, because
  matplotlib emits points and the sinks rely on a known pixel size.
"""
import io
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import matplotlib
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

DEFAULT_GRAPH_COLORS = ("#9747FF", "#FF5959", "#0DC291", "#2a0065", "#1e0047")

# matplotlib works in inches; every size in this module is expressed in pixels
# and converted with this constant so the call sites can keep using pixels.
_DPI = 100

# matplotlib salts generated SVG element ids with a fresh uuid4 per render unless
# told otherwise, which would make two renders of the same chart differ. A fixed
# salt keeps output byte-identical for identical input.
_SVG_HASH_SALT = "robusta"


@dataclass
class ChartStyle:
    """Visual configuration for a chart.

    Field names mirror the pygal ``Style`` this replaced, so playbooks that
    build a style and pass it through keep working unchanged.
    """

    background: str = "#FFFFFF"
    plot_background: str = "#FFFFFF"
    foreground: str = "#607D8B"
    foreground_strong: str = "#607D8B"
    foreground_subtle: str = "#607D8B"
    guide_stroke_color: str = "#E7EBEB"
    major_guide_stroke_color: str = "#E7EBEB"
    title_color: str = "#11383A"
    label_color: str = "#3f3f3f"
    opacity: float = 0.9
    colors: Tuple[str, ...] = DEFAULT_GRAPH_COLORS

    def color_at(self, index: int) -> str:
        if not self.colors:
            return DEFAULT_GRAPH_COLORS[index % len(DEFAULT_GRAPH_COLORS)]
        return self.colors[index % len(self.colors)]


@dataclass
class _Series:
    label: str
    values: Sequence
    stroke_style: Optional[Dict] = None
    show_dots: bool = True
    dots_size: Optional[float] = None
    stroke: bool = True
    color: Optional[str] = None
    extra: Dict = field(default_factory=dict)


def _truncate(label: str, limit: Optional[int]) -> str:
    """Match pygal's legend truncation: cut to ``limit`` chars including the ellipsis."""
    label = (label or "").replace("\n", " ").strip()
    if not limit or limit <= 0 or len(label) <= limit:
        return label
    return label[: max(limit - 1, 0)] + "…"


def _dashes_from_stroke_style(stroke_style: Optional[Dict]) -> Optional[Tuple[float, ...]]:
    """Translate an SVG ``stroke-dasharray`` into a matplotlib dash tuple."""
    if not stroke_style:
        return None
    dasharray = stroke_style.get("dasharray")
    if not dasharray:
        return None
    parts = [p.strip() for p in str(dasharray).replace(",", " ").split() if p.strip()]
    try:
        nums = [float(p) for p in parts]
    except ValueError:
        return None
    if not nums:
        return None
    # a single value means "on and off for the same length"
    return tuple(nums) if len(nums) > 1 else (nums[0], nums[0])


def _linewidth_from_stroke_style(stroke_style: Optional[Dict], default: float = 1.6) -> float:
    """pygal stroke widths are on a much coarser scale than matplotlib points."""
    if not stroke_style:
        return default
    width = stroke_style.get("width")
    if width is None:
        return default
    try:
        return max(float(width) / 5.0, 0.8)
    except (TypeError, ValueError):
        return default


def _force_svg_pixel_size(svg: bytes, width: int, height: int) -> bytes:
    """Pin the root ``<svg>`` to an exact pixel size.

    matplotlib emits ``width="921.6pt"``, which rasterizers scale by their own
    pt->px ratio. Sinks (and their tests) expect an exact pixel size, so the
    attributes are rewritten while the viewBox is left alone.
    """
    head = svg[:1024]
    head = re.sub(rb'\bwidth="[^"]*"', b'width="%d"' % width, head, count=1)
    head = re.sub(rb'\bheight="[^"]*"', b'height="%d"' % height, head, count=1)
    return head + svg[1024:]


class _BaseChart:
    """Common figure setup, title handling and SVG serialization."""

    def __init__(self, style: Optional[ChartStyle] = None, width: int = 800, height: int = 600):
        self.style = style or ChartStyle()
        self.width = width
        self.height = height
        self.title: Optional[str] = None
        self._series: List[_Series] = []

    def add(self, label: str, values, **kwargs) -> None:
        self._series.append(
            _Series(
                label=label,
                values=values,
                stroke_style=kwargs.pop("stroke_style", None),
                show_dots=kwargs.pop("show_dots", True),
                dots_size=kwargs.pop("dots_size", None),
                stroke=kwargs.pop("stroke", True),
                color=kwargs.pop("color", None),
                extra=kwargs,
            )
        )

    def _new_figure(self) -> Tuple[Figure, "object"]:
        fig = Figure(figsize=(self.width / _DPI, self.height / _DPI), dpi=_DPI)
        fig.patch.set_facecolor(self.style.background)
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.style.plot_background)
        return fig, ax

    def _apply_title(self, ax) -> None:
        if self.title:
            ax.set_title(self.title, color=self.style.title_color, fontsize=11, pad=12)

    def _draw(self, fig, ax) -> None:  # pragma: no cover - overridden
        raise NotImplementedError

    def render(self) -> bytes:
        """Render the chart and return SVG bytes."""
        fig, ax = self._new_figure()
        try:
            self._draw(fig, ax)
            buf = io.BytesIO()
            FigureCanvasSVG(fig)  # attaching the canvas is what makes savefig emit SVG
            with matplotlib.rc_context({"svg.hashsalt": _SVG_HASH_SALT}):
                fig.savefig(
                    buf,
                    format="svg",
                    facecolor=fig.get_facecolor(),
                    # drop the embedded creation date so identical input renders
                    # to identical bytes
                    metadata={"Date": None},
                )
            return _force_svg_pixel_size(buf.getvalue(), self.width, self.height)
        finally:
            fig.clear()


class XYChart(_BaseChart):
    """Line chart over ``(x, y)`` pairs - the Prometheus time-series graph."""

    def __init__(
        self,
        style: Optional[ChartStyle] = None,
        width: int = 1280,
        height: int = 500,
        show_legend: bool = True,
        truncate_legend: Optional[int] = 15,
        legend_at_bottom_columns: int = 5,
        x_label_rotation: int = 35,
    ):
        super().__init__(style=style, width=width, height=height)
        self.show_legend = show_legend
        self.truncate_legend = truncate_legend
        self.legend_at_bottom_columns = legend_at_bottom_columns
        self.x_label_rotation = x_label_rotation
        self.range: Optional[Tuple[float, float]] = None
        self.y_labels: Optional[List[float]] = None
        self.x_labels: Optional[List[float]] = None
        self.value_formatter: Callable = str
        self.x_value_formatter: Callable = str
        self.show_minor_y_labels: bool = True

    def _x_tick_positions(self, x_min: float, x_max: float) -> List[float]:
        if self.x_labels:
            return list(self.x_labels)
        # pygal spaces roughly a label per ~140px of plot width
        count = max(int(self.width / 140), 2)
        if x_max <= x_min:
            return [x_min]
        step = (x_max - x_min) / (count - 1)
        return [x_min + i * step for i in range(count)]

    def _draw(self, fig, ax) -> None:
        style = self.style

        x_values = [x for s in self._series for (x, _) in s.values]
        x_min, x_max = (min(x_values), max(x_values)) if x_values else (0, 1)

        for index, series in enumerate(self._series):
            color = series.color or style.color_at(index)
            xs = [point[0] for point in series.values]
            ys = [point[1] for point in series.values]
            line_kwargs = {
                "color": color,
                "alpha": style.opacity,
                "linewidth": _linewidth_from_stroke_style(series.stroke_style),
                "linestyle": "-" if series.stroke else "none",
                "marker": "o" if series.show_dots else "None",
                "markersize": (series.dots_size or 2.5) if series.show_dots else 0,
                "markerfacecolor": color,
                "markeredgecolor": color,
                "label": _truncate(series.label, self.truncate_legend),
                "solid_capstyle": "round",
            }
            # matplotlib rejects an explicit dashes=None, so only set it when dashed
            dashes = _dashes_from_stroke_style(series.stroke_style)
            if dashes:
                line_kwargs["dashes"] = dashes
            ax.plot(xs, ys, **line_kwargs)

        if self.range:
            ax.set_ylim(self.range[0], self.range[1])
        ax.set_xlim(x_min, x_max)

        if self.y_labels is not None:
            ax.set_yticks(list(self.y_labels))
            ax.set_yticklabels([self.value_formatter(v) for v in self.y_labels])
        if not self.show_minor_y_labels:
            ax.set_yticks(list(self.y_labels or []))

        ticks = self._x_tick_positions(x_min, x_max)
        ax.set_xticks(ticks)
        ax.set_xticklabels(
            [self.x_value_formatter(t) for t in ticks],
            rotation=self.x_label_rotation,
            ha="right",
            rotation_mode="anchor",
        )

        ax.grid(True, which="major", color=style.guide_stroke_color, linewidth=1, zorder=0)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(style.foreground)
            ax.spines[side].set_linewidth(0.8)
        ax.tick_params(colors=style.label_color, labelsize=8, length=0)

        self._apply_title(ax)
        fig.subplots_adjust(left=0.075, right=0.985, top=0.9, bottom=0.26)

        if self.show_legend and self._series:
            # anchored to the figure, not the axes, so the legend sits flush
            # against the bottom edge instead of leaving a dead band below it
            legend = fig.legend(
                loc="lower center",
                bbox_to_anchor=(0.5, 0.005),
                ncol=max(self.legend_at_bottom_columns, 1),
                frameon=False,
                fontsize=8,
                handlelength=1.4,
                handleheight=0.9,
                handletextpad=0.5,
                columnspacing=1.6,
                borderpad=0,
            )
            for text in legend.get_texts():
                text.set_color(style.label_color)


class BarChart(_BaseChart):
    """Grouped vertical bars over categorical x labels."""

    def __init__(
        self,
        style: Optional[ChartStyle] = None,
        width: int = 800,
        height: int = 600,
        x_label_rotation: int = -40,
        truncate_legend: Optional[int] = None,
    ):
        super().__init__(style=style, width=width, height=height)
        self.x_label_rotation = x_label_rotation
        self.truncate_legend = truncate_legend
        self.x_labels: List[str] = []
        self.value_formatter: Callable = str

    def _draw(self, fig, ax) -> None:
        style = self.style
        categories = list(self.x_labels or [])
        group_count = max(len(self._series), 1)
        bar_width = 0.8 / group_count
        positions = range(len(categories))

        for index, series in enumerate(self._series):
            color = series.color or style.color_at(index)
            offset = (index - (group_count - 1) / 2) * bar_width
            # negative sentinels mean "no data" - draw nothing for those slots
            heights = [v if v is not None and v >= 0 else 0 for v in series.values]
            ax.bar(
                [p + offset for p in positions],
                heights,
                width=bar_width,
                color=color,
                alpha=style.opacity,
                label=_truncate(series.label, self.truncate_legend),
                zorder=3,
            )

        ax.set_xticks(list(positions))
        ax.set_xticklabels(
            [_truncate(c, 22) for c in categories],
            rotation=self.x_label_rotation,
            ha="left" if self.x_label_rotation < 0 else "right",
            rotation_mode="anchor",
        )
        ax.yaxis.set_major_formatter(lambda value, _pos: self.value_formatter(value))
        ax.grid(True, axis="y", color=style.guide_stroke_color, linewidth=1, zorder=0)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(style.foreground)
            ax.spines[side].set_linewidth(0.8)
        ax.tick_params(colors=style.label_color, labelsize=8, length=0)

        self._apply_title(ax)
        fig.subplots_adjust(left=0.11, right=0.97, top=0.9, bottom=0.24)

        if self._series:
            legend = fig.legend(
                loc="lower center",
                bbox_to_anchor=(0.5, 0.005),
                ncol=min(len(self._series), 4),
                frameon=False,
                fontsize=8,
                handlelength=0.9,
                handleheight=0.9,
                handletextpad=0.5,
                borderpad=0,
            )
            for text in legend.get_texts():
                text.set_color(style.label_color)


def _worst_ratio(row: List[float], length: float) -> float:
    total = sum(row)
    if total <= 0 or length <= 0:
        return float("inf")
    largest, smallest = max(row), min(row)
    if smallest <= 0:
        return float("inf")
    return max((length**2) * largest / (total**2), (total**2) / ((length**2) * smallest))


def _layout_row(row: List[float], x: float, y: float, dx: float, dy: float):
    """Place one row of areas along the shorter side; return rects + leftover space."""
    covered = sum(row)
    rects = []
    if dx >= dy:
        width = covered / dy if dy else 0
        offset = y
        for area in row:
            height = area / width if width else 0
            rects.append((x, offset, width, height))
            offset += height
        return rects, (x + width, y, dx - width, dy)
    height = covered / dx if dx else 0
    offset = x
    for area in row:
        width = area / height if height else 0
        rects.append((offset, y, width, height))
        offset += width
    return rects, (x, y + height, dx, dy - height)


def squarify(areas: List[float], x: float, y: float, dx: float, dy: float):
    """Squarified treemap layout. ``areas`` must be sorted descending and already
    normalized so that their sum equals ``dx * dy``. Rects come back in input order."""
    remaining = list(areas)
    rects: List[Tuple[float, float, float, float]] = []
    row: List[float] = []
    while remaining:
        length = min(dx, dy)
        if not row:
            row.append(remaining.pop(0))
            continue
        if _worst_ratio(row, length) >= _worst_ratio(row + [remaining[0]], length):
            row.append(remaining.pop(0))
        else:
            placed, (x, y, dx, dy) = _layout_row(row, x, y, dx, dy)
            rects.extend(placed)
            row = []
    if row:
        placed, _ = _layout_row(row, x, y, dx, dy)
        rects.extend(placed)
    return rects


class TreemapChart(_BaseChart):
    """Treemap using the squarified layout, one rectangle per added series."""

    def __init__(self, style: Optional[ChartStyle] = None, width: int = 800, height: int = 600):
        super().__init__(style=style, width=width, height=height)
        self.value_formatter: Callable = str

    def _draw(self, fig, ax) -> None:
        style = self.style
        entries = []
        for index, series in enumerate(self._series):
            values = series.values if isinstance(series.values, (list, tuple)) else [series.values]
            total = sum(v for v in values if isinstance(v, (int, float)) and v > 0)
            if total > 0:
                entries.append((total, series.label, series.color or style.color_at(index)))

        ax.set_axis_off()
        self._apply_title(ax)
        if not entries:
            return

        # squarify needs descending areas; keep the original colour/label pairing
        entries.sort(key=lambda e: e[0], reverse=True)
        grand_total = sum(e[0] for e in entries)
        canvas_w, canvas_h = 100.0, 100.0
        normalized = [e[0] * canvas_w * canvas_h / grand_total for e in entries]
        rects = squarify(normalized, 0.0, 0.0, canvas_w, canvas_h)

        for (rx, ry, rw, rh), (value, label, color) in zip(rects, entries):
            ax.add_patch(
                Rectangle(
                    (rx, ry),
                    rw,
                    rh,
                    facecolor=color,
                    alpha=style.opacity,
                    edgecolor=style.background,
                    linewidth=1.5,
                )
            )
            # label only where the text actually fits; the canvas is 100 units
            # wide, and at 7pt roughly 0.78 units are needed per character
            if rw > 10 and rh > 6:
                max_chars = int(rw / 0.78)
                ax.text(
                    rx + rw / 2,
                    ry + rh / 2,
                    f"{_truncate(label, max_chars)}\n{self.value_formatter(value)}",
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="#FFFFFF",
                    linespacing=1.4,
                )

        ax.set_xlim(0, canvas_w)
        ax.set_ylim(0, canvas_h)
        ax.invert_yaxis()  # first (largest) entry lands top-left, as pygal did

        legend_handles = [
            Rectangle((0, 0), 1, 1, facecolor=color, alpha=style.opacity) for _, _, color in entries
        ]
        legend = ax.legend(
            legend_handles,
            [_truncate(label, 24) for _, label, _ in entries],
            loc="upper center",
            bbox_to_anchor=(0.5, -0.02),
            ncol=min(len(entries), 4),
            frameon=False,
            fontsize=8,
            handlelength=0.9,
            handleheight=0.9,
            handletextpad=0.5,
            borderpad=0,
        )
        for text in legend.get_texts():
            text.set_color(style.label_color)

        fig.subplots_adjust(left=0.03, right=0.97, top=0.91, bottom=0.14)
