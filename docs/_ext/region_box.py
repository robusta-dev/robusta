"""
Directives for Robusta platform URL / code blocks with an embedded region selector.

Usage in .rst::

    .. robusta-url:: https://platform.robusta.dev/account

    .. robusta-code:: bash

       curl --location --request POST 'https://api.robusta.dev/api/alerts' \
           --header 'Authorization: Bearer API-KEY'

The rendered HTML carries the ``robusta-region-box`` class; the
client-side script in ``_static/region-selector.js`` injects the
US/EU/AP selector and keeps every box on the page in sync.
"""

from html import escape

from docutils import nodes
from sphinx.util.docutils import SphinxDirective


class RobustaUrlDirective(SphinxDirective):
    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True

    def run(self):
        if self.arguments:
            url = self.arguments[0].strip()
        else:
            url = "\n".join(self.content).strip()
        if not url:
            return [
                self.state.document.reporter.warning(
                    "robusta-url requires a URL argument or content",
                    line=self.lineno,
                )
            ]

        url_attr = escape(url, quote=True)
        url_text = escape(url)
        html = (
            f'<div class="robusta-region-box robusta-region-box--url">'
            f'<div class="robusta-region-box__body">'
            f'<a class="robusta-region-box__url" href="{url_attr}">{url_text}</a>'
            f'</div></div>'
        )
        return [nodes.raw("", html, format="html")]


class RobustaCodeDirective(SphinxDirective):
    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = False

    def run(self):
        language = self.arguments[0] if self.arguments else "text"
        code = "\n".join(self.content)
        if not code.strip():
            return [
                self.state.document.reporter.warning(
                    "robusta-code requires a code block as content",
                    line=self.lineno,
                )
            ]

        container = nodes.container(classes=["robusta-region-box", "robusta-region-box--code"])
        literal = nodes.literal_block(code, code)
        literal["language"] = language
        container += literal
        return [container]


def setup(app):
    app.add_directive("robusta-url", RobustaUrlDirective)
    app.add_directive("robusta-code", RobustaCodeDirective)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
