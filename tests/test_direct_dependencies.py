import os
import tomllib


def _poetry_dependencies():
    pyproject = os.path.join(os.path.dirname(__file__), "..", "pyproject.toml")
    with open(pyproject, "rb") as f:
        return tomllib.load(f)["tool"]["poetry"]["dependencies"]


def test_cachetools_is_a_direct_dependency():
    """cachetools is imported directly, so it must be declared, not transitive (see #2060)."""
    assert "cachetools" in _poetry_dependencies()


def test_cachetools_ttlcache_importable():
    from cachetools import TTLCache

    assert TTLCache is not None
