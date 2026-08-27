import io
import os
import tarfile

import pytest

from robusta.runner.config_loader import ConfigLoader
from robusta.utils.archive import UnsafeArchiveError, safe_extract_tar


def _make_tgz(archive_path: str, members) -> str:
    """members: list of (arcname, content) tuples, or TarInfo objects for links."""
    with tarfile.open(archive_path, "w:gz") as tar:
        for member in members:
            if isinstance(member, tarfile.TarInfo):
                tar.addfile(member)
                continue
            arcname, content = member
            data = content.encode()
            info = tarfile.TarInfo(name=arcname)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return archive_path


def _symlink_member(name: str, linkname: str) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name=name)
    info.type = tarfile.SYMTYPE
    info.linkname = linkname
    return info


def _install_remote(monkeypatch, tmp_path, archive_path: str):
    """Run install_package_remote_tgz against a local archive, without pip-installing anything."""

    class _FakeResponse:
        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=65536):
            with open(archive_path, "rb") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        return
                    yield chunk

    monkeypatch.setattr("robusta.runner.config_loader.requests.get", lambda *a, **kw: _FakeResponse())
    monkeypatch.setattr(ConfigLoader, "install_package", classmethod(lambda cls, **kwargs: None))
    return ConfigLoader.install_package_remote_tgz(
        url="https://example.com/pkg.tgz", headers=None, build_isolation=True
    )


def test_remote_tgz_rejects_path_traversal(monkeypatch, tmp_path):
    archive = _make_tgz(str(tmp_path / "pkg.tgz"), [("../evil.txt", "pwned")])

    with pytest.raises(UnsafeArchiveError):
        _install_remote(monkeypatch, tmp_path, archive)

    # nothing was written outside the (already deleted) extraction dir
    assert not any(p.name == "evil.txt" for p in tmp_path.rglob("*"))


def test_remote_tgz_rejects_absolute_path(monkeypatch, tmp_path):
    archive = _make_tgz(str(tmp_path / "pkg.tgz"), [("/tmp/evil.txt", "pwned")])

    with pytest.raises(UnsafeArchiveError):
        _install_remote(monkeypatch, tmp_path, archive)


def test_safe_extract_rejects_symlink_escape(tmp_path):
    archive = _make_tgz(str(tmp_path / "pkg.tgz"), [_symlink_member("pkg/passwd", "/etc/passwd")])
    dest = tmp_path / "dest"
    dest.mkdir()

    with tarfile.open(archive, "r:gz") as tar:
        with pytest.raises(UnsafeArchiveError):
            safe_extract_tar(tar, str(dest))


def test_safe_extract_rejects_relative_symlink_escape(tmp_path):
    archive = _make_tgz(str(tmp_path / "pkg.tgz"), [_symlink_member("pkg/escape", "../../outside")])
    dest = tmp_path / "dest"
    dest.mkdir()

    with tarfile.open(archive, "r:gz") as tar:
        with pytest.raises(UnsafeArchiveError):
            safe_extract_tar(tar, str(dest))


def test_safe_extract_allows_normal_package(tmp_path):
    archive = _make_tgz(
        str(tmp_path / "pkg.tgz"),
        [("pkg/__init__.py", ""), ("pkg/pyproject.toml", "[tool.poetry]\n"), ("pkg/sub/mod.py", "x = 1\n")],
    )
    dest = tmp_path / "dest"
    dest.mkdir()

    with tarfile.open(archive, "r:gz") as tar:
        safe_extract_tar(tar, str(dest))

    assert os.path.isfile(dest / "pkg" / "__init__.py")
    assert (dest / "pkg" / "sub" / "mod.py").read_text() == "x = 1\n"
