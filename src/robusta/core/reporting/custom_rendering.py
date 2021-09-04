from datetime import datetime

from ...core.model.env_vars import DEFAULT_TIMEZONE


class RendererType:
    DATETIME = "DATETIME"


def render_value(renderer: RendererType, value):
    if renderer == RendererType.DATETIME:
        date_value = datetime.fromtimestamp(value / 1000.0)
        return date_value.astimezone(DEFAULT_TIMEZONE).strftime(
            "%b %d, %Y, %I:%M:%S %p"
        )
    raise Exception(f"Unsupported renderer type {renderer}")
