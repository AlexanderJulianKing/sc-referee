from __future__ import annotations

import csv
import gzip
import io
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal


class DelimitedReadError(ValueError):
    def __init__(
        self,
        message: str,
        *,
        reason: str,
        logical_bytes_read: int = 0,
        read_chunks: int = 0,
    ) -> None:
        super().__init__(message)
        self.reason = reason
        self.logical_bytes_read = logical_bytes_read
        self.read_chunks = read_chunks


@dataclass(frozen=True)
class DelimitedFormat:
    table_format: Literal["csv", "tsv"]
    delimiter: Literal[",", "\t"]
    content_encoding: Literal["identity", "gzip"]


@dataclass(frozen=True)
class BoundedDelimitedHeader:
    names: tuple[str, ...]
    quoted_text: str
    end_line: int
    table_format: Literal["csv", "tsv"]
    content_encoding: Literal["identity", "gzip"]
    logical_bytes_read: int
    read_chunks: int


@dataclass(frozen=True)
class BoundedDelimitedContent:
    content: bytes
    table_format: Literal["csv", "tsv"]
    content_encoding: Literal["gzip"]
    raw_file_bytes: int
    logical_bytes_read: int
    read_chunks: int
    raw_byte_ceiling: int
    content_byte_ceiling: int
    logical_read_byte_ceiling: int
    chunk_byte_ceiling: int

    def __post_init__(self) -> None:
        if len(self.content) > self.content_byte_ceiling:
            raise ValueError("decoded delimited content exceeds its byte ceiling")
        if self.logical_bytes_read != len(self.content):
            raise ValueError("decoded delimited byte accounting is inconsistent")
        if self.logical_bytes_read > self.logical_read_byte_ceiling:
            raise ValueError("decoded delimited logical reads exceed their ceiling")
        if self.raw_file_bytes > self.raw_byte_ceiling or self.read_chunks < 0:
            raise ValueError("decoded delimited raw-byte or chunk accounting is inconsistent")

    def lock_projection(self) -> dict[str, int | str]:
        return {
            "table_format": self.table_format,
            "content_encoding": self.content_encoding,
            "raw_file_bytes": self.raw_file_bytes,
            "logical_bytes_read": self.logical_bytes_read,
            "read_chunks": self.read_chunks,
            "raw_byte_ceiling": self.raw_byte_ceiling,
            "content_byte_ceiling": self.content_byte_ceiling,
            "logical_read_byte_ceiling": self.logical_read_byte_ceiling,
            "chunk_byte_ceiling": self.chunk_byte_ceiling,
        }


def classify_delimited_path(path: str) -> DelimitedFormat | None:
    lowered = path.casefold()
    formats: tuple[
        tuple[
            str,
            Literal["csv", "tsv"],
            Literal[",", "\t"],
            Literal["identity", "gzip"],
        ],
        ...,
    ] = (
        (".csv.gz", "csv", ",", "gzip"),
        (".tsv.gz", "tsv", "\t", "gzip"),
        (".csv", "csv", ",", "identity"),
        (".tsv", "tsv", "\t", "identity"),
    )
    for ending, table_format, delimiter, content_encoding in formats:
        if lowered.endswith(ending):
            return DelimitedFormat(
                table_format=table_format,
                delimiter=delimiter,
                content_encoding=content_encoding,
            )
    return None


def read_bounded_delimited_header(
    payload: bytes,
    path: str,
    *,
    raw_byte_ceiling: int,
    header_byte_ceiling: int,
    logical_read_byte_ceiling: int,
    chunk_byte_ceiling: int,
    checkpoint: Callable[[], None] | None = None,
) -> BoundedDelimitedHeader:
    """Read exactly one strict UTF-8 CSV/TSV logical record under explicit ceilings."""

    file_format = classify_delimited_path(path)
    if file_format is None:
        raise DelimitedReadError(
            "path is not a supported delimited format",
            reason="unsupported_path",
        )
    if (
        min(
            raw_byte_ceiling,
            header_byte_ceiling,
            logical_read_byte_ceiling,
            chunk_byte_ceiling,
        )
        <= 0
    ):
        raise ValueError("delimited read ceilings must be positive")
    if header_byte_ceiling >= logical_read_byte_ceiling:
        raise ValueError("logical read ceiling must reserve at least one header sentinel byte")
    if len(payload) > raw_byte_ceiling:
        raise DelimitedReadError(
            "delimited payload exceeds the raw-byte ceiling",
            reason="raw_budget_exceeded",
        )

    raw_stream = io.BytesIO(payload)
    stream: io.BufferedIOBase | gzip.GzipFile
    if file_format.content_encoding == "gzip":
        stream = gzip.GzipFile(fileobj=raw_stream, mode="rb")
    else:
        stream = raw_stream

    logical = bytearray()
    logical_bytes_read = 0
    read_chunks = 0
    reached_eof = False
    while not reached_eof:
        remaining = logical_read_byte_ceiling - logical_bytes_read
        if remaining <= 0:
            raise DelimitedReadError(
                "delimited header exceeds the logical-read ceiling",
                reason="logical_budget_exceeded",
                logical_bytes_read=logical_bytes_read,
                read_chunks=read_chunks,
            )
        if checkpoint is not None and file_format.content_encoding == "gzip":
            checkpoint()
        try:
            chunk = stream.readline(min(chunk_byte_ceiling, remaining))
        except (EOFError, OSError) as error:
            raise DelimitedReadError(
                "gzip stream could not be read safely",
                reason="invalid_compression",
                logical_bytes_read=logical_bytes_read,
                read_chunks=read_chunks,
            ) from error
        if not chunk:
            reached_eof = True
        else:
            logical.extend(chunk)
            logical_bytes_read += len(chunk)
            read_chunks += 1
            if len(logical) > header_byte_ceiling:
                raise DelimitedReadError(
                    "delimited header exceeds the header-byte ceiling",
                    reason="header_budget_exceeded",
                    logical_bytes_read=logical_bytes_read,
                    read_chunks=read_chunks,
                )

        if not reached_eof and (not chunk or not chunk.endswith(b"\n")):
            continue
        if not logical:
            return BoundedDelimitedHeader(
                names=(),
                quoted_text="",
                end_line=1,
                table_format=file_format.table_format,
                content_encoding=file_format.content_encoding,
                logical_bytes_read=logical_bytes_read,
                read_chunks=read_chunks,
            )
        try:
            text = bytes(logical).decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise DelimitedReadError(
                "delimited header is not strict UTF-8",
                reason="non_utf8",
                logical_bytes_read=logical_bytes_read,
                read_chunks=read_chunks,
            ) from error
        reader = csv.reader(
            io.StringIO(text, newline=""),
            delimiter=file_format.delimiter,
            strict=True,
        )
        try:
            header = next(reader)
        except StopIteration:
            header = []
        except csv.Error as error:
            if not reached_eof and "unexpected end of data" in str(error).casefold():
                continue
            raise DelimitedReadError(
                "first delimited record could not be parsed safely",
                reason="invalid_header",
                logical_bytes_read=logical_bytes_read,
                read_chunks=read_chunks,
            ) from error
        end_line = max(1, reader.line_num)
        return BoundedDelimitedHeader(
            names=tuple(header),
            quoted_text="\n".join(text.splitlines()[:end_line]),
            end_line=end_line,
            table_format=file_format.table_format,
            content_encoding=file_format.content_encoding,
            logical_bytes_read=logical_bytes_read,
            read_chunks=read_chunks,
        )

    raise AssertionError("bounded delimited reader terminated without a result")


def read_bounded_delimited_content(
    payload: bytes,
    path: str,
    *,
    raw_byte_ceiling: int,
    content_byte_ceiling: int,
    logical_read_byte_ceiling: int,
    chunk_byte_ceiling: int,
    checkpoint: Callable[[], None] | None = None,
) -> BoundedDelimitedContent:
    """Fully decompress one exact gzip CSV/TSV payload under explicit logical ceilings."""

    file_format = classify_delimited_path(path)
    if file_format is None or file_format.content_encoding != "gzip":
        raise DelimitedReadError(
            "path is not a supported gzip-delimited format",
            reason="unsupported_path",
        )
    if (
        min(
            raw_byte_ceiling,
            content_byte_ceiling,
            logical_read_byte_ceiling,
            chunk_byte_ceiling,
        )
        <= 0
    ):
        raise ValueError("delimited read ceilings must be positive")
    if content_byte_ceiling >= logical_read_byte_ceiling:
        raise ValueError("logical read ceiling must reserve at least one content sentinel byte")
    if len(payload) > raw_byte_ceiling:
        raise DelimitedReadError(
            "compressed delimited payload exceeds the raw-byte ceiling",
            reason="raw_budget_exceeded",
        )

    stream = gzip.GzipFile(fileobj=io.BytesIO(payload), mode="rb")
    logical = bytearray()
    logical_bytes_read = 0
    read_chunks = 0
    while True:
        remaining = logical_read_byte_ceiling - logical_bytes_read
        if remaining <= 0:
            raise DelimitedReadError(
                "compressed delimited content exceeds the logical-read ceiling",
                reason="logical_budget_exceeded",
                logical_bytes_read=logical_bytes_read,
                read_chunks=read_chunks,
            )
        if checkpoint is not None:
            checkpoint()
        try:
            chunk = stream.read(min(chunk_byte_ceiling, remaining))
        except (EOFError, OSError) as error:
            raise DelimitedReadError(
                "gzip stream could not be read and validated safely",
                reason="invalid_compression",
                logical_bytes_read=logical_bytes_read,
                read_chunks=read_chunks,
            ) from error
        if not chunk:
            break
        logical.extend(chunk)
        logical_bytes_read += len(chunk)
        read_chunks += 1
        if len(logical) > content_byte_ceiling:
            raise DelimitedReadError(
                "compressed delimited content exceeds the content-byte ceiling",
                reason="content_budget_exceeded",
                logical_bytes_read=logical_bytes_read,
                read_chunks=read_chunks,
            )
    return BoundedDelimitedContent(
        content=bytes(logical),
        table_format=file_format.table_format,
        content_encoding="gzip",
        raw_file_bytes=len(payload),
        logical_bytes_read=logical_bytes_read,
        read_chunks=read_chunks,
        raw_byte_ceiling=raw_byte_ceiling,
        content_byte_ceiling=content_byte_ceiling,
        logical_read_byte_ceiling=logical_read_byte_ceiling,
        chunk_byte_ceiling=chunk_byte_ceiling,
    )
