import os
import tarfile
from typing import List


class UnsafeArchiveError(Exception):
    """Raised when a tar archive contains a member that would be extracted outside the target directory."""


def _is_within(directory: str, target: str) -> bool:
    directory = os.path.realpath(directory)
    target = os.path.realpath(target)
    return target == directory or target.startswith(directory + os.sep)


def _validate_members(tar: tarfile.TarFile, path: str) -> List[tarfile.TarInfo]:
    members = tar.getmembers()
    for member in members:
        if member.isdev():
            raise UnsafeArchiveError(f"Archive contains a device/fifo member: {member.name}")

        if os.path.isabs(member.name) or member.name.startswith("/"):
            raise UnsafeArchiveError(f"Archive contains a member with an absolute path: {member.name}")

        if not _is_within(path, os.path.join(path, member.name)):
            raise UnsafeArchiveError(f"Archive contains a member escaping the target directory: {member.name}")

        if member.issym() or member.islnk():
            # link targets are resolved relative to the directory holding the link
            link_base = os.path.join(path, os.path.dirname(member.name))
            if os.path.isabs(member.linkname) or not _is_within(path, os.path.join(link_base, member.linkname)):
                raise UnsafeArchiveError(
                    f"Archive contains a link escaping the target directory: {member.name} -> {member.linkname}"
                )

    return members


def safe_extract_tar(tar: tarfile.TarFile, path: str) -> None:
    """
    Extract a tar archive into ``path``, refusing archives whose members would be written outside of it.

    Guards against path traversal ("zip slip"), absolute member paths, escaping symlinks/hardlinks and
    device nodes. Raises ``UnsafeArchiveError`` without extracting anything if the archive is unsafe.
    """
    if hasattr(tarfile, "data_filter"):  # python 3.12+, and 3.10.12+/3.11.4+ backports
        # pre-validate so that nothing is written before an unsafe member is detected
        _validate_members(tar, path)
        try:
            tar.extractall(path=path, filter="data")
        except tarfile.FilterError as e:
            raise UnsafeArchiveError(f"Refusing to extract unsafe archive: {e}") from e
    else:
        tar.extractall(path=path, members=_validate_members(tar, path))
