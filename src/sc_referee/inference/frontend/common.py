from __future__ import annotations

from dataclasses import dataclass, field

from sc_referee.inference.ids import content_digest
from sc_referee.source_ast import ParsedSource, parse_sources, strip_magics, to_python


@dataclass(frozen=True)
class SourceUnit:
    source_index: int
    original: str
    normalized: str
    language: str
    digest: str
    parsed: ParsedSource = field(compare=False, repr=False)

    @classmethod
    def from_text(cls, text: str, *, language: str = "python", source_index: int = 0):
        normalized = strip_magics(to_python(text)) if language == "python" else text
        if language == "python":
            parsed = parse_sources([text])[0]
            parsed.source_index = source_index
        else:
            parsed = ParsedSource(source_index, None)
        return cls(source_index, text, normalized, language, content_digest(text), parsed)


def adapt_sources(sources) -> tuple[SourceUnit, ...]:
    """Use the shipped parser exactly once; never import or execute analyzed code."""
    inputs = tuple(sources)
    originals = tuple(source.original if isinstance(source, SourceUnit) else str(source)
                      for source in inputs)
    parsed = parse_sources(originals)
    result = []
    for index, item in enumerate(parsed):
        supplied = inputs[index]
        if isinstance(supplied, SourceUnit):
            language = supplied.language
            normalized = supplied.normalized
            if language != "python":
                item = ParsedSource(index, None)
        else:
            language = "python"
            normalized = strip_magics(to_python(originals[index]))
        result.append(SourceUnit(index, originals[index], normalized, language,
                                 content_digest(originals[index]), item))
    return tuple(result)
