import json
import logging
import os
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

# Get the directory where our templates are stored
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))


class SlackTemplateLoader:
    """
    Loads and renders Jinja2 templates for Slack messages.
    """

    def __init__(self):
        """Initialize the template environment."""
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATE_DIR),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Cache for templates
        self._templates: Dict[str, Template] = {}

    def get_template(self, template_name: str) -> Template:
        """
        Get a template by name, loading from file if not already cached.

        Args:
            template_name: The name of the template file (e.g., "header.j2")

        Returns:
            A Jinja2 Template object
        """
        if template_name not in self._templates:
            try:
                self._templates[template_name] = self.env.get_template(template_name)
            except Exception as e:
                logging.error(f"Error loading template {template_name}: {e}")
                # Return a simple default template as fallback
                return Template("Template loading error")

        return self._templates[template_name]

    def render_to_blocks(self, template: Template, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Render a Jinja2 Template object using the provided context and parse the result as JSON to get Slack blocks.
        Args:
            template: A Jinja2 Template object
            context: Dictionary of variables to pass to the template
        Returns:
            List of Slack block objects (dictionaries)
        """
        try:
            rendered = template.render(**context)
            blocks = []
            for block_str in rendered.strip().split("\n\n"):
                if not block_str.strip():
                    continue
                try:
                    # Try to parse as JSON, but if it fails, log and skip
                    block = json.loads(block_str)
                    blocks.append(block)
                except json.JSONDecodeError as e:
                    logging.exception(f"Error parsing JSON from template output: {e}")
                    logging.warning(f"Problematic JSON (repr): {repr(block_str)}")
                    continue  # Skip this block and continue
                except Exception as e:
                    logging.error(f"Unexpected error parsing block: {e}")
                    logging.warning(f"Problematic JSON (repr): {repr(block_str)}")
                    continue
            return blocks
        except Exception as e:
            logging.error(f"Error rendering template: {e}")
            return []

    def render_custom_template_to_blocks(self, custom_template: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            template = Template(custom_template)
            return self.render_to_blocks(template, context)
        except Exception as e:
            logging.error(f"Error rendering custom template: {e}")
            return self.render_default_template_to_blocks(context)

    def render_default_template_to_blocks(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        DEFAULT_TEMPLATE_NAME="header.j2"
        template = self.get_template(DEFAULT_TEMPLATE_NAME)
        return self.render_to_blocks(template, context)


# Singleton instance
template_loader = SlackTemplateLoader()
