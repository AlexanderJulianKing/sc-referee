from __future__ import annotations

from sc_referee.calculation_checks.core import FrozenCalculationInput
from sc_referee.delimited_io import classify_delimited_path


def bounded_table_text(
    table: FrozenCalculationInput,
    *,
    byte_ceiling: int,
    error_type: type[ValueError],
    label: str,
) -> tuple[str, str]:
    """Return one bounded exact logical table and its declared delimiter."""

    file_format = classify_delimited_path(table.path)
    if file_format is None:
        raise error_type(f"{label} path is not a supported CSV or TSV path")
    if file_format.content_encoding == "gzip" and table.decoded_delimited_content is None:
        raise error_type(f"{label} gzip body is unavailable in the bounded decoded view")
    content = table.inspection_content
    if len(content) > byte_ceiling:
        raise error_type(f"{label} exceeds the decompressed-byte ceiling")
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise error_type(f"{label} is not strict UTF-8") from error
    return text, file_format.delimiter
