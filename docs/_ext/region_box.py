"""
Directives and role for Robusta platform URL / code components with an
embedded region selector.

Usage in .rst::

    .. robusta-url:: https://platform.robusta.dev/account

    .. robusta-code:: bash

       curl --location --request POST 'https://api.robusta.dev/api/alerts' \
           --header 'Authorization: Bearer API-KEY'

    Sign up at :robusta-url:`https://platform.robusta.dev/signup` to get started.

    Or with custom link text:

    Visit :robusta-url:`our platform <https://platform.robusta.dev/signup>` today.

The rendered HTML carries ``robusta-region-box`` (block) or
``robusta-region-inline`` (inline) classes; the client-side script in
``_static/region-selector.js`` injects the US/EU/AP selector and keeps
every region-aware component on the page in sync.
"""

import re
from html import escape

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util import parselinenos
from sphinx.util.docutils import SphinxDirective


_LABELLED_URL_RE = re.compile(r"^\s*(.+?)\s*<\s*([^<>\s]+)\s*>\s*$", re.DOTALL)


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
    option_spec = {
        "emphasize-lines": directives.unchanged_required,
    }

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

        emphasize_spec = self.options.get("emphasize-lines")
        if emphasize_spec:
            try:
                nlines = len(code.split("\n"))
                hl_lines = [x + 1 for x in parselinenos(emphasize_spec, nlines) if 0 <= x < nlines]
            except ValueError:
                hl_lines = []
            if hl_lines:
                literal["highlight_args"] = {"hl_lines": hl_lines}

        container += literal
        return [container]


class RobustaRegionPickerDirective(SphinxDirective):
    """Standalone region picker: a 'Select Region' label + dropdown, no URL."""

    has_content = False
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True

    def run(self):
        label = (self.arguments[0].strip() if self.arguments else "Select Region")
        html = (
            f'<div class="robusta-region-picker">'
            f'<span class="robusta-region-picker__label">{escape(label)}</span>'
            f'<span class="robusta-region-inline robusta-region-picker__host"></span>'
            f"</div>"
        )
        return [nodes.raw("", html, format="html")]


def robusta_url_role(name, rawtext, text, lineno, inliner, options=None, content=None):
    """Inline ``:robusta-url:`URL``` or ``:robusta-url:`label <URL>```."""
    raw_text = nodes.unescape(text)
    match = _LABELLED_URL_RE.match(raw_text)
    if match:
        label = match.group(1).strip()
        url = match.group(2).strip()
    else:
        url = raw_text.strip()
        label = url
    if not label:
        label = url
    if not url:
        msg = inliner.reporter.error(
            "robusta-url role requires a URL", line=lineno
        )
        return [inliner.problematic(rawtext, rawtext, msg)], [msg]

    html = (
        f'<span class="robusta-region-inline">'
        f'<a class="robusta-region-inline__url" href="{escape(url, quote=True)}">'
        f"{escape(label)}</a>"
        f"</span>"
    )
    return [nodes.raw("", html, format="html")], []


def setup(app):
    app.add_directive("robusta-url", RobustaUrlDirective)
    app.add_directive("robusta-code", RobustaCodeDirective)
    app.add_directive("robusta-region-picker", RobustaRegionPickerDirective)
    app.add_role("robusta-url", robusta_url_role)
    return {
        "version": "0.3",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
