from __future__ import annotations

import hashlib
import json
import os
import secrets
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, TypedDict

from sc_referee.core.ids import canonical_json, semantic_digest

MAX_CASE_FILES = 32
MAX_CASE_DIRECTORIES = 32
MAX_CASE_ENTRIES = 64
MAX_CASE_DEPTH = 8
MAX_CASE_FILE_BYTES = 10 * 1024 * 1024
MAX_CASE_TOTAL_BYTES = 50 * 1024 * 1024


class QualificationIOError(RuntimeError):
    """Raised when qualification input or output cannot be accessed safely."""


@dataclass(frozen=True)
class RootedRead:
    """Bytes and digest obtained from the same verified file descriptor."""

    relative_path: str
    data: bytes
    content_digest: str


class CaseTreeFile(TypedDict):
    path: str
    content_digest: str
    byte_length: int
    executable: bool


class CaseTreeSnapshot(TypedDict):
    source_relative_path: str
    retained_files: list[CaseTreeFile]
    case_tree_digest: str
    file_count: int
    total_bytes: int


@dataclass(frozen=True)
class RootedTreeFile:
    """One immutable file captured from a descriptor-rooted tree scan."""

    relative_path: str
    data: bytes
    content_digest: str
    mode: int

    @property
    def byte_length(self) -> int:
        return len(self.data)


@dataclass(frozen=True)
class RootedTreeRead:
    """A complete tree whose bytes and inventory survived two identical scans."""

    files: tuple[RootedTreeFile, ...]
    total_bytes: int

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(item.relative_path for item in self.files)

    def read(self, relative_path: str, *, max_bytes: int | None = None) -> RootedRead:
        canonical_relative_path(relative_path)
        if max_bytes is not None and (
            isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 0
        ):
            raise QualificationIOError("max_bytes must be a nonnegative integer or None.")
        matches = [item for item in self.files if item.relative_path == relative_path]
        if len(matches) != 1:
            raise QualificationIOError("Qualification tree input is absent.")
        item = matches[0]
        if max_bytes is not None and item.byte_length > max_bytes:
            raise QualificationIOError("Qualification input exceeds its byte limit.")
        return RootedRead(
            relative_path=item.relative_path,
            data=item.data,
            content_digest=item.content_digest,
        )

    def read_bytes(self, relative_path: str, *, max_bytes: int | None = None) -> bytes:
        return self.read(relative_path, max_bytes=max_bytes).data


@dataclass(frozen=True)
class _TreeLimits:
    max_files: int | None
    max_directories: int | None
    max_entries: int | None
    max_depth: int | None
    max_file_bytes: int | None
    max_total_bytes: int | None


@dataclass(frozen=True)
class _DescriptorState:
    device: int
    inode: int
    mode: int
    links: int
    size: int
    modified_ns: int
    changed_ns: int

    @classmethod
    def from_stat(cls, value: os.stat_result) -> _DescriptorState:
        return cls(
            device=value.st_dev,
            inode=value.st_ino,
            mode=value.st_mode,
            links=value.st_nlink,
            size=value.st_size,
            modified_ns=value.st_mtime_ns,
            changed_ns=value.st_ctime_ns,
        )

    @property
    def identity(self) -> tuple[int, int]:
        return self.device, self.inode


@dataclass(frozen=True)
class _OpenDirectory:
    descriptor: int
    initial_state: _DescriptorState
    parent_descriptor: int | None
    entry_name: str | None


@dataclass(frozen=True)
class _TreeEntry:
    path: str
    kind: str
    state: _DescriptorState


@dataclass
class _TreeScan:
    retained_files: list[CaseTreeFile]
    entries: list[_TreeEntry]
    file_modes: dict[str, int]
    payloads: dict[str, bytes]
    directory_count: int = 1
    entry_count: int = 0
    total_bytes: int = 0


def _tree_limits(
    *,
    max_files: int | None,
    max_directories: int | None,
    max_entries: int | None,
    max_depth: int | None,
    max_file_bytes: int | None,
    max_total_bytes: int | None,
) -> _TreeLimits:
    values = {
        "max_files": max_files,
        "max_directories": max_directories,
        "max_entries": max_entries,
        "max_depth": max_depth,
        "max_file_bytes": max_file_bytes,
        "max_total_bytes": max_total_bytes,
    }
    for label, value in values.items():
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise QualificationIOError(f"{label} must be a nonnegative integer or None.")
    return _TreeLimits(
        max_files=max_files,
        max_directories=max_directories,
        max_entries=max_entries,
        max_depth=max_depth,
        max_file_bytes=max_file_bytes,
        max_total_bytes=max_total_bytes,
    )


def _tree_scans_match(first: _TreeScan, second: _TreeScan) -> bool:
    return (
        second.retained_files == first.retained_files
        and second.entries == first.entries
        and second.file_modes == first.file_modes
        and second.payloads == first.payloads
        and second.directory_count == first.directory_count
        and second.entry_count == first.entry_count
        and second.total_bytes == first.total_bytes
    )


def _required_open_flag(name: str) -> int:
    value = getattr(os, name, None)
    if not isinstance(value, int):
        raise QualificationIOError(f"This platform does not provide required {name} support.")
    return value


def _directory_open_flags() -> int:
    return (
        os.O_RDONLY
        | _required_open_flag("O_DIRECTORY")
        | _required_open_flag("O_NOFOLLOW")
        | getattr(os, "O_CLOEXEC", 0)
    )


def _file_read_flags() -> int:
    return os.O_RDONLY | _required_open_flag("O_NOFOLLOW") | getattr(os, "O_CLOEXEC", 0)


def _file_create_flags() -> int:
    return (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | _required_open_flag("O_NOFOLLOW")
        | getattr(os, "O_CLOEXEC", 0)
    )


def canonical_relative_path(raw: str) -> tuple[str, ...]:
    """Validate and split a canonical relative POSIX path."""

    if not isinstance(raw, str) or not raw:
        raise QualificationIOError("Qualification paths must be non-empty strings.")
    if "\\" in raw or "\x00" in raw:
        raise QualificationIOError("Qualification paths must use canonical POSIX syntax.")
    parsed = PurePosixPath(raw)
    if (
        parsed.is_absolute()
        or parsed.as_posix() != raw
        or not parsed.parts
        or any(part in {"", ".", ".."} for part in parsed.parts)
    ):
        raise QualificationIOError("Qualification paths must be canonical and relative.")
    return parsed.parts


class RootedReader:
    """Read files beneath one descriptor-pinned, non-symlink directory root."""

    def __init__(self, root: Path | str) -> None:
        self._root_path = os.path.abspath(os.fspath(root))
        self._root_descriptor = -1
        descriptor = -1
        try:
            entry_before = os.lstat(self._root_path)
            if not stat.S_ISDIR(entry_before.st_mode) or stat.S_ISLNK(entry_before.st_mode):
                raise QualificationIOError(
                    "Qualification root must be a real, non-symlink directory."
                )
            descriptor = os.open(self._root_path, _directory_open_flags())
            opened = os.fstat(descriptor)
            entry_after = os.lstat(self._root_path)
            if (
                not stat.S_ISDIR(opened.st_mode)
                or (
                    opened.st_dev,
                    opened.st_ino,
                )
                != (entry_before.st_dev, entry_before.st_ino)
                or (
                    opened.st_dev,
                    opened.st_ino,
                )
                != (entry_after.st_dev, entry_after.st_ino)
            ):
                raise QualificationIOError("Qualification root changed while it was opened.")
            os.set_inheritable(descriptor, False)
            self._root_descriptor = descriptor
            descriptor = -1
            self._root_identity = (opened.st_dev, opened.st_ino)
        except QualificationIOError:
            raise
        except OSError as error:
            raise QualificationIOError("Qualification root could not be opened safely.") from error
        finally:
            if descriptor >= 0:
                os.close(descriptor)

    @property
    def root(self) -> Path:
        return Path(self._root_path)

    @property
    def closed(self) -> bool:
        return self._root_descriptor < 0

    def close(self) -> None:
        if self._root_descriptor >= 0:
            os.close(self._root_descriptor)
            self._root_descriptor = -1

    def __enter__(self) -> RootedReader:
        if self.closed:
            raise QualificationIOError("Qualification root reader is closed.")
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def read(self, relative_path: str, *, max_bytes: int | None = None) -> RootedRead:
        """Read and hash a regular file through verified directory descriptors."""

        if max_bytes is not None and (
            isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 0
        ):
            raise QualificationIOError("max_bytes must be a nonnegative integer or None.")
        parts = canonical_relative_path(relative_path)
        directories: list[_OpenDirectory] = []
        file_descriptor = -1
        try:
            directories = self._open_parent(parts)
            parent = directories[-1].descriptor
            entry_before = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
            if not stat.S_ISREG(entry_before.st_mode):
                raise QualificationIOError("Qualification input must be a regular file.")
            file_descriptor = os.open(parts[-1], _file_read_flags(), dir_fd=parent)
            before = _DescriptorState.from_stat(os.fstat(file_descriptor))
            if not stat.S_ISREG(before.mode) or before.identity != (
                entry_before.st_dev,
                entry_before.st_ino,
            ):
                raise QualificationIOError("Qualification input changed while it was opened.")

            chunks: list[bytes] = []
            content_hash = hashlib.sha256()
            observed_size = 0
            while True:
                chunk = os.read(file_descriptor, 1024 * 1024)
                if not chunk:
                    break
                observed_size += len(chunk)
                if max_bytes is not None and observed_size > max_bytes:
                    raise QualificationIOError("Qualification input exceeds its byte limit.")
                chunks.append(chunk)
                content_hash.update(chunk)

            after = _DescriptorState.from_stat(os.fstat(file_descriptor))
            if observed_size != before.size or after != before:
                raise QualificationIOError("Qualification input mutated while it was read.")
            entry_after = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
            if (entry_after.st_dev, entry_after.st_ino) != after.identity:
                raise QualificationIOError("Qualification input was replaced while it was read.")
            self._verify_directories(directories)
            return RootedRead(
                relative_path=relative_path,
                data=b"".join(chunks),
                content_digest=f"sha256:{content_hash.hexdigest()}",
            )
        except QualificationIOError:
            raise
        except OSError as error:
            raise QualificationIOError(
                f"Qualification input {relative_path!r} could not be read safely."
            ) from error
        finally:
            if file_descriptor >= 0:
                os.close(file_descriptor)
            self._close_directories(directories)

    def read_bytes(self, relative_path: str, *, max_bytes: int | None = None) -> bytes:
        return self.read(relative_path, max_bytes=max_bytes).data

    def read_canonical_json(self, relative_path: str, *, max_bytes: int | None = None) -> Any:
        rooted_read = self.read(relative_path, max_bytes=max_bytes)
        try:
            value = json.loads(rooted_read.data)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise QualificationIOError("Qualification JSON input is malformed.") from error
        if rooted_read.data != (canonical_json(value) + "\n").encode("utf-8"):
            raise QualificationIOError(
                "Qualification JSON input must be canonical and end in one newline."
            )
        return value

    def read_case_tree(
        self,
        source_relative_path: str | None = None,
        *,
        max_files: int | None = None,
        max_directories: int | None = None,
        max_entries: int | None = None,
        max_depth: int | None = None,
        max_file_bytes: int | None = None,
        max_total_bytes: int | None = None,
    ) -> RootedTreeRead:
        """Capture one immutable descriptor-rooted tree after two identical full scans."""

        limits = _tree_limits(
            max_files=max_files,
            max_directories=max_directories,
            max_entries=max_entries,
            max_depth=max_depth,
            max_file_bytes=max_file_bytes,
            max_total_bytes=max_total_bytes,
        )
        source_parts = (
            () if source_relative_path is None else canonical_relative_path(source_relative_path)
        )
        source_directories: list[_OpenDirectory] = []
        try:
            source_directories = self._open_directory_parts(source_parts)
            source_root = source_directories[-1].descriptor
            first = _TreeScan(retained_files=[], entries=[], file_modes={}, payloads={})
            self._scan_case_tree(
                source_descriptor=source_root,
                destination_descriptor=None,
                prefix=PurePosixPath(),
                depth=0,
                scan=first,
                forbidden_source_identity=None,
                limits=limits,
            )
            if not first.retained_files:
                raise QualificationIOError("Qualification case tree must not be empty.")
            self._verify_directories(source_directories)

            second = _TreeScan(retained_files=[], entries=[], file_modes={}, payloads={})
            self._scan_case_tree(
                source_descriptor=source_root,
                destination_descriptor=None,
                prefix=PurePosixPath(),
                depth=0,
                scan=second,
                forbidden_source_identity=None,
                limits=limits,
            )
            if not _tree_scans_match(first, second):
                raise QualificationIOError(
                    "Qualification case tree changed between its verified reads."
                )
            self._verify_directories(source_directories)
            files = tuple(
                RootedTreeFile(
                    relative_path=str(item["path"]),
                    data=first.payloads[str(item["path"])],
                    content_digest=str(item["content_digest"]),
                    mode=first.file_modes[str(item["path"])],
                )
                for item in first.retained_files
            )
            return RootedTreeRead(files=files, total_bytes=first.total_bytes)
        except QualificationIOError:
            raise
        except OSError as error:
            raise QualificationIOError(
                "Qualification case tree could not be read safely."
            ) from error
        finally:
            self._close_directories(source_directories)

    def snapshot_case_tree(
        self,
        source_relative_path: str,
        destination: Path | str,
    ) -> CaseTreeSnapshot:
        """Copy one finite case tree without executing or following any project file."""

        source_parts = canonical_relative_path(source_relative_path)
        source_directories: list[_OpenDirectory] = []
        destination_directories: list[_OpenDirectory] = []
        try:
            source_directories = self._open_directory_parts(source_parts)
            source_root = source_directories[-1].descriptor
            source_root_state = _DescriptorState.from_stat(os.fstat(source_root))
            if not stat.S_ISDIR(source_root_state.mode):
                raise QualificationIOError("Qualification case-tree source is not a directory.")

            with RootedReader(destination) as destination_reader:
                destination_directories = destination_reader._open_directory_parts(())
                destination_root = destination_directories[-1].descriptor
                destination_state = _DescriptorState.from_stat(os.fstat(destination_root))
                if destination_state.identity == source_root_state.identity:
                    raise QualificationIOError(
                        "Qualification case-tree source and destination must be distinct."
                    )
                if os.listdir(destination_root):
                    raise QualificationIOError("Qualification case-tree destination must be empty.")
                if _DescriptorState.from_stat(os.fstat(destination_root)) != destination_state:
                    raise QualificationIOError(
                        "Qualification case-tree destination changed before copying."
                    )

                limits = _TreeLimits(
                    max_files=MAX_CASE_FILES,
                    max_directories=MAX_CASE_DIRECTORIES,
                    max_entries=MAX_CASE_ENTRIES,
                    max_depth=MAX_CASE_DEPTH,
                    max_file_bytes=MAX_CASE_FILE_BYTES,
                    max_total_bytes=MAX_CASE_TOTAL_BYTES,
                )
                first = _TreeScan(retained_files=[], entries=[], file_modes={}, payloads={})
                self._scan_case_tree(
                    source_descriptor=source_root,
                    destination_descriptor=destination_root,
                    prefix=PurePosixPath(),
                    depth=0,
                    scan=first,
                    forbidden_source_identity=destination_state.identity,
                    limits=limits,
                )
                if not first.retained_files:
                    raise QualificationIOError("Qualification case tree must not be empty.")
                self._verify_directories(source_directories)

                second = _TreeScan(retained_files=[], entries=[], file_modes={}, payloads={})
                self._scan_case_tree(
                    source_descriptor=source_root,
                    destination_descriptor=None,
                    prefix=PurePosixPath(),
                    depth=0,
                    scan=second,
                    forbidden_source_identity=destination_state.identity,
                    limits=limits,
                )
                if not _tree_scans_match(first, second):
                    raise QualificationIOError(
                        "Qualification case tree changed after it was copied."
                    )
                self._verify_directories(source_directories)

                copied = _TreeScan(retained_files=[], entries=[], file_modes={}, payloads={})
                destination_reader._scan_case_tree(
                    source_descriptor=destination_root,
                    destination_descriptor=None,
                    prefix=PurePosixPath(),
                    depth=0,
                    scan=copied,
                    forbidden_source_identity=source_root_state.identity,
                    limits=limits,
                )
                if (
                    copied.retained_files != first.retained_files
                    or copied.file_modes != first.file_modes
                    or copied.payloads != first.payloads
                    or [(item.path, item.kind) for item in copied.entries]
                    != [(item.path, item.kind) for item in first.entries]
                    or copied.directory_count != first.directory_count
                    or copied.entry_count != first.entry_count
                    or copied.total_bytes != first.total_bytes
                ):
                    raise QualificationIOError(
                        "Qualification case-tree destination does not match its source."
                    )
                destination_reader._verify_directory_identities(destination_directories)
                retained_files = list(first.retained_files)
                return {
                    "source_relative_path": source_relative_path,
                    "retained_files": retained_files,
                    "case_tree_digest": semantic_digest(retained_files),
                    "file_count": len(retained_files),
                    "total_bytes": first.total_bytes,
                }
        except QualificationIOError:
            raise
        except OSError as error:
            raise QualificationIOError(
                "Qualification case tree could not be snapshotted safely."
            ) from error
        finally:
            self._close_directories(destination_directories)
            self._close_directories(source_directories)

    def _scan_case_tree(
        self,
        *,
        source_descriptor: int,
        destination_descriptor: int | None,
        prefix: PurePosixPath,
        depth: int,
        scan: _TreeScan,
        forbidden_source_identity: tuple[int, int] | None,
        limits: _TreeLimits,
    ) -> None:
        if limits.max_depth is not None and depth > limits.max_depth:
            raise QualificationIOError("Qualification case tree exceeds the finite depth ceiling.")
        directory_before = _DescriptorState.from_stat(os.fstat(source_descriptor))
        if not stat.S_ISDIR(directory_before.mode):
            raise QualificationIOError("Qualification case-tree entry is not a directory.")
        if (
            forbidden_source_identity is not None
            and directory_before.identity == forbidden_source_identity
        ):
            raise QualificationIOError(
                "Qualification case-tree destination cannot be nested in its source."
            )
        names = sorted(os.listdir(source_descriptor))
        for name in names:
            try:
                name.encode("utf-8", errors="strict")
            except UnicodeEncodeError as error:
                raise QualificationIOError(
                    "Qualification case-tree names must be strict UTF-8."
                ) from error
            relative = (prefix / name).as_posix()
            canonical_relative_path(relative)
            scan.entry_count += 1
            if limits.max_entries is not None and scan.entry_count > limits.max_entries:
                raise QualificationIOError(
                    "Qualification case tree exceeds the finite entry-count ceiling."
                )
            entry = os.stat(name, dir_fd=source_descriptor, follow_symlinks=False)
            entry_state = _DescriptorState.from_stat(entry)
            if stat.S_ISLNK(entry_state.mode):
                raise QualificationIOError(
                    "Qualification case trees cannot contain symbolic links."
                )
            if stat.S_ISDIR(entry_state.mode):
                scan.directory_count += 1
                if (
                    limits.max_directories is not None
                    and scan.directory_count > limits.max_directories
                ):
                    raise QualificationIOError(
                        "Qualification case tree exceeds the finite directory-count ceiling."
                    )
                source_child = -1
                destination_child = -1
                try:
                    source_child = os.open(
                        name,
                        _directory_open_flags(),
                        dir_fd=source_descriptor,
                    )
                    os.set_inheritable(source_child, False)
                    opened_source = _DescriptorState.from_stat(os.fstat(source_child))
                    if opened_source != entry_state:
                        raise QualificationIOError(
                            "Qualification case-tree directory changed before traversal."
                        )
                    if destination_descriptor is not None:
                        os.mkdir(name, mode=0o700, dir_fd=destination_descriptor)
                        destination_entry = os.stat(
                            name,
                            dir_fd=destination_descriptor,
                            follow_symlinks=False,
                        )
                        if not stat.S_ISDIR(destination_entry.st_mode):
                            raise QualificationIOError(
                                "Qualification snapshot destination entry is not a directory."
                            )
                        destination_child = os.open(
                            name,
                            _directory_open_flags(),
                            dir_fd=destination_descriptor,
                        )
                        os.set_inheritable(destination_child, False)
                        opened_destination = _DescriptorState.from_stat(os.fstat(destination_child))
                        if opened_destination.identity != (
                            destination_entry.st_dev,
                            destination_entry.st_ino,
                        ):
                            raise QualificationIOError(
                                "Qualification snapshot directory was replaced."
                            )
                    self._scan_case_tree(
                        source_descriptor=source_child,
                        destination_descriptor=(
                            destination_child if destination_descriptor is not None else None
                        ),
                        prefix=prefix / name,
                        depth=depth + 1,
                        scan=scan,
                        forbidden_source_identity=forbidden_source_identity,
                        limits=limits,
                    )
                    source_entry_after = os.stat(
                        name, dir_fd=source_descriptor, follow_symlinks=False
                    )
                    source_after = _DescriptorState.from_stat(os.fstat(source_child))
                    if source_after != opened_source or source_after.identity != (
                        source_entry_after.st_dev,
                        source_entry_after.st_ino,
                    ):
                        raise QualificationIOError(
                            "Qualification case-tree directory mutated or was replaced."
                        )
                    if destination_child >= 0:
                        assert destination_descriptor is not None
                        destination_after = _DescriptorState.from_stat(os.fstat(destination_child))
                        destination_entry_after = os.stat(
                            name,
                            dir_fd=destination_descriptor,
                            follow_symlinks=False,
                        )
                        if destination_after.identity != (
                            destination_entry_after.st_dev,
                            destination_entry_after.st_ino,
                        ):
                            raise QualificationIOError(
                                "Qualification snapshot directory was replaced."
                            )
                    scan.entries.append(_TreeEntry(relative, "directory", source_after))
                finally:
                    if destination_child >= 0:
                        os.close(destination_child)
                    if source_child >= 0:
                        os.close(source_child)
                continue
            if not stat.S_ISREG(entry_state.mode):
                raise QualificationIOError(
                    "Qualification case trees may contain only regular files."
                )
            payload, stable_state = self._read_stable_regular_at(
                source_descriptor,
                name,
                entry_state,
                max_bytes=limits.max_file_bytes,
            )
            scan.total_bytes += len(payload)
            if limits.max_total_bytes is not None and scan.total_bytes > limits.max_total_bytes:
                raise QualificationIOError(
                    "Qualification case tree exceeds the finite total-byte ceiling."
                )
            scan.file_modes[relative] = stat.S_IMODE(stable_state.mode)
            scan.payloads[relative] = payload
            record: CaseTreeFile = {
                "path": relative,
                "content_digest": f"sha256:{hashlib.sha256(payload).hexdigest()}",
                "byte_length": len(payload),
                "executable": bool(stable_state.mode & 0o111),
            }
            scan.retained_files.append(record)
            scan.entries.append(_TreeEntry(relative, "file", stable_state))
            if limits.max_files is not None and len(scan.retained_files) > limits.max_files:
                raise QualificationIOError(
                    "Qualification case tree exceeds the finite file-count ceiling."
                )
            if destination_descriptor is not None:
                self._write_regular_exclusive_at(
                    destination_descriptor,
                    name,
                    payload,
                    stat.S_IMODE(stable_state.mode),
                )
        directory_after = _DescriptorState.from_stat(os.fstat(source_descriptor))
        if directory_after != directory_before:
            raise QualificationIOError(
                "Qualification case-tree directory mutated during traversal."
            )

    @staticmethod
    def _read_stable_regular_at(
        directory_descriptor: int,
        name: str,
        expected: _DescriptorState,
        *,
        max_bytes: int | None,
    ) -> tuple[bytes, _DescriptorState]:
        descriptor = -1
        try:
            descriptor = os.open(name, _file_read_flags(), dir_fd=directory_descriptor)
            os.set_inheritable(descriptor, False)
            before = _DescriptorState.from_stat(os.fstat(descriptor))
            if not stat.S_ISREG(before.mode) or before != expected:
                raise QualificationIOError(
                    "Qualification case-tree file changed before it was read."
                )
            if max_bytes is not None and before.size > max_bytes:
                raise QualificationIOError(
                    "Qualification case-tree file exceeds the finite byte ceiling."
                )
            chunks: list[bytes] = []
            observed_size = 0
            while True:
                read_size = 1024 * 1024
                if max_bytes is not None:
                    read_size = min(read_size, max_bytes + 1 - observed_size)
                chunk = os.read(descriptor, read_size)
                if not chunk:
                    break
                chunks.append(chunk)
                observed_size += len(chunk)
                if max_bytes is not None and observed_size > max_bytes:
                    raise QualificationIOError(
                        "Qualification case-tree file exceeds the finite byte ceiling."
                    )
            after = _DescriptorState.from_stat(os.fstat(descriptor))
            entry_after = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
            if observed_size != before.size or after != before:
                raise QualificationIOError(
                    "Qualification case-tree file mutated while it was read."
                )
            if after.identity != (entry_after.st_dev, entry_after.st_ino):
                raise QualificationIOError(
                    "Qualification case-tree file was replaced while it was read."
                )
            return b"".join(chunks), after
        finally:
            if descriptor >= 0:
                os.close(descriptor)

    @staticmethod
    def _write_regular_exclusive_at(
        directory_descriptor: int,
        name: str,
        payload: bytes,
        mode: int,
    ) -> None:
        descriptor = -1
        try:
            descriptor = os.open(
                name,
                _file_create_flags(),
                0o600,
                dir_fd=directory_descriptor,
            )
            os.set_inheritable(descriptor, False)
            opened = _DescriptorState.from_stat(os.fstat(descriptor))
            if not stat.S_ISREG(opened.mode):
                raise QualificationIOError("Qualification snapshot output is not a regular file.")
            written = 0
            while written < len(payload):
                count = os.write(descriptor, payload[written:])
                if count <= 0:
                    raise QualificationIOError(
                        "Qualification snapshot output write did not progress."
                    )
                written += count
            os.fchmod(descriptor, mode)
            os.fsync(descriptor)
            after = _DescriptorState.from_stat(os.fstat(descriptor))
            entry_after = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
            if (
                after.identity != opened.identity
                or after.size != len(payload)
                or stat.S_IMODE(after.mode) != mode
                or after.identity != (entry_after.st_dev, entry_after.st_ino)
            ):
                raise QualificationIOError("Qualification snapshot output mutated or was replaced.")
        finally:
            if descriptor >= 0:
                os.close(descriptor)

    def _open_parent(self, parts: tuple[str, ...]) -> list[_OpenDirectory]:
        return self._open_directory_parts(parts[:-1])

    def _open_directory_parts(self, parts: tuple[str, ...]) -> list[_OpenDirectory]:
        if self.closed:
            raise QualificationIOError("Qualification root reader is closed.")
        root_entry = os.lstat(self._root_path)
        root_descriptor = os.dup(self._root_descriptor)
        os.set_inheritable(root_descriptor, False)
        root_state = _DescriptorState.from_stat(os.fstat(root_descriptor))
        if root_state.identity != self._root_identity or root_state.identity != (
            root_entry.st_dev,
            root_entry.st_ino,
        ):
            os.close(root_descriptor)
            raise QualificationIOError("Qualification root was replaced.")
        directories = [
            _OpenDirectory(
                descriptor=root_descriptor,
                initial_state=root_state,
                parent_descriptor=None,
                entry_name=None,
            )
        ]
        try:
            for part in parts:
                parent = directories[-1].descriptor
                entry_before = os.stat(part, dir_fd=parent, follow_symlinks=False)
                if not stat.S_ISDIR(entry_before.st_mode):
                    raise QualificationIOError(
                        "Qualification paths may traverse only real directories."
                    )
                descriptor = -1
                try:
                    descriptor = os.open(part, _directory_open_flags(), dir_fd=parent)
                    os.set_inheritable(descriptor, False)
                    opened_state = _DescriptorState.from_stat(os.fstat(descriptor))
                    entry_after = os.stat(part, dir_fd=parent, follow_symlinks=False)
                    if (
                        not stat.S_ISDIR(opened_state.mode)
                        or opened_state.identity != (entry_before.st_dev, entry_before.st_ino)
                        or opened_state.identity != (entry_after.st_dev, entry_after.st_ino)
                    ):
                        raise QualificationIOError(
                            "Qualification directory changed while it was opened."
                        )
                    directories.append(
                        _OpenDirectory(
                            descriptor=descriptor,
                            initial_state=opened_state,
                            parent_descriptor=parent,
                            entry_name=part,
                        )
                    )
                    descriptor = -1
                finally:
                    if descriptor >= 0:
                        os.close(descriptor)
            return directories
        except BaseException:
            self._close_directories(directories)
            raise

    def _verify_directories(self, directories: list[_OpenDirectory]) -> None:
        for opened in reversed(directories):
            after = _DescriptorState.from_stat(os.fstat(opened.descriptor))
            if after != opened.initial_state:
                raise QualificationIOError("Qualification directory mutated while input was read.")
            if opened.parent_descriptor is None:
                entry = os.lstat(self._root_path)
            else:
                assert opened.entry_name is not None
                entry = os.stat(
                    opened.entry_name,
                    dir_fd=opened.parent_descriptor,
                    follow_symlinks=False,
                )
            if (entry.st_dev, entry.st_ino) != after.identity:
                raise QualificationIOError(
                    "Qualification directory was replaced while input was read."
                )

    def _verify_directory_identities(self, directories: list[_OpenDirectory]) -> None:
        for opened in reversed(directories):
            after = _DescriptorState.from_stat(os.fstat(opened.descriptor))
            if after.identity != opened.initial_state.identity:
                raise QualificationIOError("Qualification output directory changed.")
            if opened.parent_descriptor is None:
                entry = os.lstat(self._root_path)
            else:
                assert opened.entry_name is not None
                entry = os.stat(
                    opened.entry_name,
                    dir_fd=opened.parent_descriptor,
                    follow_symlinks=False,
                )
            if (entry.st_dev, entry.st_ino) != after.identity:
                raise QualificationIOError("Qualification output directory was replaced.")

    @staticmethod
    def _close_directories(directories: list[_OpenDirectory]) -> None:
        for opened in reversed(directories):
            os.close(opened.descriptor)


def write_canonical_json_exclusive(
    root: Path | str,
    relative_path: str,
    value: Any,
    *,
    mode: int = 0o600,
) -> str:
    """Create one canonical-JSON output without following links or overwriting data."""

    if isinstance(mode, bool) or not isinstance(mode, int) or mode < 0 or mode > 0o777:
        raise QualificationIOError("Output mode must be a permission mode from 0o000 to 0o777.")
    payload = (canonical_json(value) + "\n").encode("utf-8")
    parts = canonical_relative_path(relative_path)
    with RootedReader(root) as rooted:
        directories: list[_OpenDirectory] = []
        descriptor = -1
        temporary_name = f".qualification-{secrets.token_hex(16)}.tmp"
        temporary_created = False
        published_created = False
        temporary_identity: tuple[int, int] | None = None
        try:
            directories = rooted._open_parent(parts)
            parent = directories[-1].descriptor
            descriptor = os.open(
                temporary_name,
                _file_create_flags(),
                mode,
                dir_fd=parent,
            )
            temporary_created = True
            os.set_inheritable(descriptor, False)
            initial = _DescriptorState.from_stat(os.fstat(descriptor))
            temporary_identity = initial.identity
            if not stat.S_ISREG(initial.mode):
                raise QualificationIOError("Qualification output is not a regular file.")
            written = 0
            while written < len(payload):
                count = os.write(descriptor, payload[written:])
                if count <= 0:
                    raise QualificationIOError("Qualification output write did not progress.")
                written += count
            os.fsync(descriptor)
            final = _DescriptorState.from_stat(os.fstat(descriptor))
            if final.identity != initial.identity or final.size != len(payload):
                raise QualificationIOError("Qualification output mutated while it was written.")
            temporary_entry = os.stat(temporary_name, dir_fd=parent, follow_symlinks=False)
            if (temporary_entry.st_dev, temporary_entry.st_ino) != final.identity:
                raise QualificationIOError("Qualification output was replaced before publication.")
            try:
                os.link(
                    temporary_name,
                    parts[-1],
                    src_dir_fd=parent,
                    dst_dir_fd=parent,
                    follow_symlinks=False,
                )
                published_created = True
            except FileExistsError as error:
                raise QualificationIOError(
                    "Qualification output already exists; overwrite is forbidden."
                ) from error
            published = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
            if (published.st_dev, published.st_ino) != final.identity:
                raise QualificationIOError("Qualification output publication was replaced.")
            os.unlink(temporary_name, dir_fd=parent)
            temporary_created = False
            after_publication = _DescriptorState.from_stat(os.fstat(descriptor))
            published_after = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
            if (
                after_publication.identity != final.identity
                or after_publication.links != 1
                or after_publication.size != len(payload)
                or (published_after.st_dev, published_after.st_ino) != after_publication.identity
            ):
                raise QualificationIOError("Qualification output changed after publication.")
            rooted._verify_directory_identities(directories)
            published_created = False
            return f"sha256:{hashlib.sha256(payload).hexdigest()}"
        except QualificationIOError:
            raise
        except OSError as error:
            raise QualificationIOError(
                "Qualification output could not be created safely."
            ) from error
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            if published_created and directories:
                parent = directories[-1].descriptor
                try:
                    entry = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
                    if temporary_identity == (entry.st_dev, entry.st_ino):
                        os.unlink(parts[-1], dir_fd=parent)
                except OSError:
                    pass
            if temporary_created and directories:
                parent = directories[-1].descriptor
                try:
                    entry = os.stat(temporary_name, dir_fd=parent, follow_symlinks=False)
                    if temporary_identity == (entry.st_dev, entry.st_ino):
                        os.unlink(temporary_name, dir_fd=parent)
                except OSError:
                    pass
            rooted._close_directories(directories)
