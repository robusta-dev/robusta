#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Robusta documentation build configuration file, created by
# sphinx-quickstart on Wed Apr 28 13:48:20 2021.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# add the root robusta directory to the path so that playbooks/ becomes importable
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / Path("_ext")))

# -- General configuration ------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.graphviz",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinxcontrib.images",
    "autorobusta",
]

images_config = {
    "override_image_directive": True,
}

autodoc_mock_imports = ["prometheus_api_client"]
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    #'special-members': '__init__',
    "undoc-members": True,
    #'exclude-members': '__weakref__'
}
autoclass_content = "both"
add_module_names = False


# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
source_suffix = [".rst", ".md"]

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "Robusta"
copyright = "2021, Robusta"
author = "Natan Yellin"

# The short X.Y version.
version = "DOCS_VERSION_PLACEHOLDER"
# The full version, including alpha/beta/rc tags.
release = "DOCS_RELEASE_PLACEHOLDER"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The name of the Pygments (syntax highlighting) style to use.
# pygments_style = "manni"
# pygments_dark_style = "monokai"
pygments_style = "witchhazel.WitchHazelStyle"
pygments_dark_style = "witchhazel.WitchHazelStyle"

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

# html_theme_path = [furo.get_pygments_stylesheet()]
html_theme = "furo"
html_theme_options = {
    "sidebar_hide_name": True,
    "light_logo": "logo.png",
    "dark_logo": "logo-dark.png",
    "light_css_variables": {
        # for branding purposes this should really be #d9534f, but it doesn't look as good
        "color-brand-primary": "#7253ed",
        "color-brand-content": "#7253ed",
    },
    "dark_css_variables": {
        # "color-brand-primary": "#7C4DFF",
        # "color-brand-content": "#7C4DFF",
        # "color-sidebar-link-text": "black",
    },
}
# html_title = ""

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

html_css_files = [
    "custom.css",
]

# html_logo = "_static/logo.png"


def setup(app):
    app.add_css_file("custom.css")
