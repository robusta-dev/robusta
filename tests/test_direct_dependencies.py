import os

import toml


def _poetry_dependencies():
    pyproject = os.path.join(os.path.dirname(__file__), "..", "pyproject.toml")
    return toml.load(pyproject)["tool"]["poetry"]["dependencies"]


def test_cachetools_is_a_direct_dependency():
    """cachetools is imported directly, so it must be declared, not transitive (see #2060)."""
    assert "cachetools" in _poetry_dependencies()


def test_cachetools_ttlcache_importable():
    from cachetools import TTLCache

    assert TTLCache is not None
