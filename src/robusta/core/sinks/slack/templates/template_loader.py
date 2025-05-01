import json
import logging
import os
from typing import Dict, Any, Optional, List, Tuple

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

    def render_to_blocks(self, template_name: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Render a template using the provided context and parse the result as JSON to get Slack blocks.
        
        Args:
            template_name: The name of the template file
            context: Dictionary of variables to pass to the template
            
        Returns:
            List of Slack block objects (dictionaries)
        """
        template = self.get_template(template_name)
        
        try:
            rendered = template.render(**context)
            
            # Split by newlines to get multiple blocks and parse each as JSON
            blocks = []
            for block_str in rendered.strip().split("\n\n"):
                if block_str.strip():
                    try:
                        block = json.loads(block_str)
                        blocks.append(block)
                    except json.JSONDecodeError as e:
                        logging.error(f"Error parsing JSON from template output: {e}")
                        logging.debug(f"Problematic JSON: {block_str}")
            
            return blocks
        except Exception as e:
            logging.error(f"Error rendering template {template_name}: {e}")
            return []


# Singleton instance
template_loader = SlackTemplateLoader()