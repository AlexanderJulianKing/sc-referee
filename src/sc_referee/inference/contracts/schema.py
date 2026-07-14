from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SummaryBinding:
    module: str
    symbol: str
    version: str
    package_or_source_digest: str
    summary_digest: str


@dataclass(frozen=True)
class EffectContract:
    reads: tuple[str, ...] = ()
    writes: tuple[str, ...] = ()
    return_from: tuple[int, ...] = ()
    allocates: bool = False
    egresses: tuple[str, ...] = ()


@dataclass(frozen=True)
class FunctionSummary:
    binding: SummaryBinding
    effects: EffectContract
    ports: tuple[object, ...] = ()


@dataclass(frozen=True)
class CalleeBinding:
    module: str
    symbol: str
    version: str
    package_or_source_digest: str
    summary_digest: str


def binding_is_exact(binding) -> bool:
    return binding is not None and all((
        getattr(binding, "module", None), getattr(binding, "symbol", None),
        getattr(binding, "version", None), getattr(binding, "package_or_source_digest", None),
        getattr(binding, "summary_digest", None),
    ))
