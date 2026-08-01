# ADR-0027: Require tiered independent approval for detector promotion

## Status

Superseded in part by ADR-0037.

## Context

Maturity labels determine whether a detector may produce demonstrated Findings and therefore cannot be self-awarded casually.

## Decision

Experimental release requires maintainer review. The original decision required human scientific reviewers for validated and publication-grade promotion. ADR-0037 replaces that mandatory-human requirement with conservative cross-provider coding-agent adjudication and explicit review-basis disclosure. Maintainer approval, public qualification reports, and emergency demotion remain. See SA-FR-085.

## Consequences

- Small teams can iterate experimentally.
- Higher maturity has credible independent review.
- Qualification reports and emergency demotion become mandatory.
