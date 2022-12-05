from datetime import datetime
from pygal.style import Style

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


charts_style = Style(
    background='#F2F2F2',
    plot_background='#F2F2F2',
    value_background = 'rgba(229, 229, 229, 1)',
    foreground='#9EAEB0',
    foreground_strong = '#9EAEB0',
    foreground_subtle = '#9EAEB0',
    guide_stroke_dasharray = '0,0',
    major_guide_stroke_dasharray = '0,0',
    guide_stroke_color = '#E7EBEB',
    major_guide_stroke_color = '#E7EBEB',
    opacity='.6',
    opacity_hover='.9',
    transition='400ms ease-in',
    colors=('#9747FF', '#7d17ff', '#4b00ad', '#2a0065', '#1e0047'))
