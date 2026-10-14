from datetime import datetime
from typing import Tuple

from robusta.core.model.env_vars import DEFAULT_TIMEZONE
from robusta.core.reporting.charts import ChartStyle


class RendererType:
    DATETIME = "DATETIME"


def render_value(renderer: RendererType, value):
    if renderer == RendererType.DATETIME:
        date_value = datetime.fromtimestamp(value / 1000.0)
        return date_value.astimezone(DEFAULT_TIMEZONE).strftime("%b %d, %Y, %I:%M:%S %p")
    raise Exception(f"Unsupported renderer type {renderer}")


def charts_style(
        graph_colors: Tuple = ("#9747FF", "#FF5959", "#0DC291", "#2a0065", "#1e0047"),
) -> ChartStyle:
    return ChartStyle(colors=graph_colors)
