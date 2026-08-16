from datetime import datetime
from typing import Tuple

from robusta.core.model.env_vars import DEFAULT_TIMEZONE
from robusta.core.reporting.charts import DEFAULT_GRAPH_COLORS, ChartStyle


class RendererType:
    DATETIME = "DATETIME"


def render_value(renderer: RendererType, value):
    if renderer == RendererType.DATETIME:
        date_value = datetime.fromtimestamp(value / 1000.0)
        return date_value.astimezone(DEFAULT_TIMEZONE).strftime("%b %d, %Y, %I:%M:%S %p")
    raise Exception(f"Unsupported renderer type {renderer}")


def charts_style(
        graph_colors: Tuple = DEFAULT_GRAPH_COLORS,
) -> ChartStyle:
    """Robusta's chart palette. Kept as a function (and exported through
    ``robusta.api``) so playbooks can build a styled chart in one call."""
    return ChartStyle(colors=tuple(graph_colors))
