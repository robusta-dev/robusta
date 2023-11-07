import logging
from datetime import datetime
from typing import Tuple, Optional
import tempfile

from robusta.core.model.env_vars import DEFAULT_TIMEZONE


class RendererType:
    DATETIME = "DATETIME"


def render_value(renderer: RendererType, value):
    if renderer == RendererType.DATETIME:
        date_value = datetime.fromtimestamp(value / 1000.0)
        return date_value.astimezone(DEFAULT_TIMEZONE).strftime("%b %d, %Y, %I:%M:%S %p")
    raise Exception(f"Unsupported renderer type {renderer}")


def charts_style(
        graph_colors: Tuple = ("#9747FF", "#FF5959", "#0DC291", "#2a0065", "#1e0047"),
):
    from pygal.style import Style

    return Style(
        background="#FFFFFF",
        plot_background="#FFFFFF",
        value_background="rgba(229, 229, 229, 1)",
        foreground="#607D8B",
        foreground_strong="#607D8B",
        foreground_subtle="#607D8B",
        guide_stroke_dasharray="0,0",
        major_guide_stroke_dasharray="0,0",
        guide_stroke_color="#E7EBEB",
        major_guide_stroke_color="#E7EBEB",
        opacity=".6",
        opacity_hover=".9",
        transition="400ms ease-in",
        colors=graph_colors,
    )


class PlotCustomCSS:
    _css_file_path = None

    def __init__(self):
        if PlotCustomCSS._css_file_path is None:
            try:
                custom_css = '''
                  {{ id }}.title {
                    fill: #11383A;
                  }
    
                  {{ id }}.legends .legend text {
                    fill: #3f3f3f;
                  }
              
                  {{ id }}.axis.y text {
                    fill: #3f3f3f;
                  }
    
                  {{ id }}.axis.x text {
                    fill: #3f3f3f;
                  }
                '''

                with tempfile.NamedTemporaryFile(delete=False, suffix='.css') as f:
                    f.write(custom_css.encode('utf-8'))
                    f.flush()
                    PlotCustomCSS._css_file_path = f.name
            except Exception as e:
                logging.error(f"Error during initializing PlotCustomCSS: {e}", exc_info=True)
                PlotCustomCSS._css_file_path = None

    def get_css_file_path(self) -> Optional[str]:
        return self._css_file_path
