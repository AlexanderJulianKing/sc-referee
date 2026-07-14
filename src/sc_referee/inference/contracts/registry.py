from __future__ import annotations

from dataclasses import dataclass

from sc_referee.inference.contracts.schema import CalleeBinding, FunctionSummary


@dataclass(frozen=True)
class Resolution:
    status: str
    summary: FunctionSummary | None = None
    reason: str | None = None


class SummaryRegistry:
    def __init__(self, summaries=()):
        self._summaries = {(s.binding.module, s.binding.symbol, s.binding.version,
                            s.binding.package_or_source_digest, s.binding.summary_digest): s
                           for s in summaries}

    def register(self, summary: FunctionSummary):
        key = (summary.binding.module, summary.binding.symbol, summary.binding.version,
               summary.binding.package_or_source_digest, summary.binding.summary_digest)
        self._summaries[key] = summary

    def resolve_summary(self, binding: CalleeBinding) -> Resolution:
        key = (binding.module, binding.symbol, binding.version,
               binding.package_or_source_digest, binding.summary_digest)
        summary = self._summaries.get(key)
        if summary is None:
            return Resolution("unresolved", reason="exact module/symbol/version/package/summary digest required")
        return Resolution("exact", summary)


def resolve_summary(binding: CalleeBinding, registry: SummaryRegistry) -> Resolution:
    return registry.resolve_summary(binding)

