# Experiment 0002: Bounded observed mean-difference lineage

- **Status:** Active local experiment; not a qualified detector capability
- **Date:** 2026-07-28
- **Scope:** Static Python plus local CSV, one exact filtered mean-difference profile

## Purpose

Test whether the general-project controller can reconstruct useful observed computation and claim
lineage without executing project-authored code, treating scientist intent as execution evidence,
or qualifying a detector prematurely.

## Exact envelope

The auditor-owned verifier applies only when the immutable snapshot contains exactly one function
matching all of these constraints:

- two list comprehensions select finite numeric values from one literal CSV input path;
- both selections use the same literal outcome column and compare one literal group column to two
  literal group values;
- the function returns left arithmetic mean minus right arithmetic mean; and
- the function has one literal local `Path(...)` call site whose public Operation and input/output
  Artifact edges resolve exactly.

Unsupported Python, missing or unsafe inputs, nonnumeric values, multiple matching computations,
and graph disagreements abstain locally. Project modules are never imported and project code is
never executed.

## Claim-link rule

A deterministic directional Markdown Claim receives a link only when one verified result uniquely
matches all three case-folded literal fields:

- claim comparison left side equals the operation's left group;
- claim comparison right side equals the operation's right group; and
- the exact claimed object equals the operation's outcome column.

The verified `ObservedResult` may have complete value-to-code/input lineage because sc-referee
independently recomputed it from immutable bytes. The Claim remains `partial`: no observed
report-generation or project-execution edge establishes that the computation produced the exact
report wording. Scientist Answers and model proposals cannot supply that missing link.

An optional source-level report edge is admitted only when one literal
`Path.write_text`/`write_bytes` target is the selected exact-digest report and its single data
expression contains a whitelisted direct call to one uniquely defined supported computation. The
write Operation then consumes that computation's result Artifact. This establishes static source
dataflow only. It does not establish that the call or writer ran, that the writer produced the
snapshotted bytes, or that the result produced the claim wording. The result may cross one
top-level assignment chain only when the supported function is defined first and uniquely bound,
every alias has one binding in the inspected module, each assignment consumes only earlier aliases
through the same whitelisted expression grammar, and a later top-level writer consumes the chain.
The chain is capped at eight alias edges. Rebinding, deletion, imports or nested-scope shadowing,
use-before-definition, over-limit chains, conditional/nested writers, format specifications, and
opaque render calls abstain. The same bounded grammar may operate inside one uniquely bound,
undecorated, synchronous, module-level, zero-parameter renderer function without requiring or
inferring a call site. Every executable statement in that renderer must be either a uniquely bound
assignment carrying the same supported result or a literal report write consuming it; the optional
first statement may be a docstring. Parameters, branches, loops, exception/with blocks, returns,
unrelated calls or assignments, mutation, local `Path`/`str`/`repr` shadowing, nested renderers, and
over-limit chains cause the whole renderer to abstain. Module-level `str`/`repr` shadowing also
disables those otherwise whitelisted wrappers.

One additional interprocedural shape is admitted when the renderer has exactly one required
positional parameter and exactly one direct, unconditional, module-level call after its unique
definition. The sole positional argument must resolve through the existing bounded module grammar
to exactly one supported result Artifact. The parameter is then treated as one more bounded alias
edge inside the same all-or-nothing straight-line renderer grammar. Missing or multiple calls,
calls in nested or conditional scopes, keyword arguments, defaults, multiple parameters,
parameter reassignment, opaque transforms, and combined chains beyond eight edges abstain. This is
still source-level dataflow; recognizing the call syntax does not claim that Python executed it.

The same unique-call profile may contain additional required positional presentation parameters
when exactly one call argument resolves to exactly one supported result and every other argument
is a constant-only expression under the existing bounded render grammar. Those literal-bound
parameter names may occur only inside that grammar alongside the result; they cannot establish a
dynamic output path, pass through an opaque transform, or carry a second result. The renderer body
remains all-or-nothing and straight-line, every parameter must remain unmodified, the report target
must still be one literal `Path`, and the shared eight-edge result-alias ceiling still applies.
Defaults, keyword binding, dynamic presentation arguments, multiple result arguments, missing or
multiple calls, or a literal-only call with no supported result all abstain. Exact literal
presentation does not establish scientific semantics or runtime execution.

One of those literal-bound parameters may also supply the report target, but only as a direct safe
repository-relative POSIX string argument at the unique call and only when the renderer uses the
unmodified parameter as the sole argument to `Path(...)` immediately receiving `write_text` or
`write_bytes`. At most one parameter-bound output write is allowed in the renderer. This
reconstructs the same exact output Artifact identity and writer edge as a
literal `Path` in the function body. Module aliases, string wrappers, absolute or traversal paths,
backslashes, empty/dot components, parameter rebinding, other path constructors, and target
transforms abstain. It remains source-level path identity, not evidence that the call or write ran.

The unique call may bind positional-or-keyword parameters by exact Python name when the renderer
still has only required positional parameters. Positional arguments bind in order; named arguments
must bind every remaining non-positional-only parameter exactly once. Missing, extra, duplicate,
positional-only-by-keyword, keyword-unpacking, defaulted, keyword-only, variadic, or dynamic
literal-argument forms abstain. Call-site keyword order has no authority; the declared parameter
order controls the deterministic binding. Exactly one bound expression must still carry one
supported result and every other bound expression must remain constant-only.

A separate direct formatter shape is admitted only when a uniquely bound, undecorated,
synchronous, module-level function has only required positional parameters, no annotations, an
optional docstring, and exactly one `return`. That formatter must have exactly one call in the
module, and the call must be the writer's complete data argument after the formatter definition.
Arguments bind under the same exact positional/keyword rules; exactly one carries the supported
result. The returned expression must use only constants, bound parameters, f-strings without format
specifications, string addition, and `str`/`repr` unshadowed by either module or parameter
bindings. A parameter named `Path` also invalidates a renderer path edge. Assignments, multiple
calls, call
aliases, decorators, annotations, defaults, opaque transforms, missing/two results, or use before
definition abstain. The writer records `direct_static_formatter_call`; it does not execute the
formatter or claim a runtime transformation.

The same formatter result may cross a strictly linear chain of top-level single-name assignments
before the writer. Every name must have one module binding and exactly one load in the entire
module; each nonterminal load must occur in the next accepted assignment, and only the terminal
name may be the complete data argument of exactly one later top-level literal
`write_text`/`write_bytes` call. The formatter call remains unique, and the combined result,
formatter, and assignment flow remains inside the shared eight-edge ceiling. Forks, merges,
rebindings, deletion, tuple targets, extra reads, unused intermediates, multiple writers,
writer-before-assignment, opaque transforms, and nested or conditional consumers invalidate the
whole chain. A one-assignment writer records `single_static_formatter_assignment`; a longer chain
records `static_formatter_assignment_chain`. Neither form infers formatter or writer execution.

## Safety boundaries

- This experiment schedules no detector and admits no Finding.
- The outcome column name is not represented as a known measurement scale.
- Direction agreement is not required for linking; requiring agreement would hide potential
  contradictions. Detector evaluation remains separately gated and unqualified.
- A single nonmatching result is not linked merely because it is unique.
- Public records and replay are authoritative; SQLite remains generated.

## Exit evidence

- `test_general_audit_reconstructs_only_bounded_partial_claim_lineage` verifies the positive path,
  public records, zero Findings, and model-free replay.
- `test_bounded_lineage_rejects_an_unaligned_claim_object` verifies the lexical hard negative.
- `test_publication_answer_preserves_and_binds_precomputed_observed_lineage` verifies that a later
  typed publication Answer preserves and binds the precomputed result without granting it new
  authority.
- `test_exact_static_result_artifact_flow_reaches_report_lineage_without_execution` verifies the
  exact source-level result-Artifact/writer edge, partial Claim grade, zero Findings, and replay.
- `test_indirect_python_value_does_not_invent_static_report_result_flow` and
  `test_python_parser_abstains_from_result_flow_when_function_binding_is_ambiguous` verify bounded
  abstention.
- `test_python_parser_links_only_one_module_assignment_alias_before_the_writer`,
  `test_python_parser_abstains_from_out_of_order_shadowed_or_nested_result_flow`, and
  `test_exact_single_assignment_result_alias_reaches_report_lineage` verify the exact alias path,
  mutation/scope/order abstention, public records, and replay.
- `test_python_parser_follows_only_bounded_module_assignment_chains` and
  `test_exact_assignment_chain_result_flow_reaches_report_lineage` verify ordered multi-hop render
  flow, the eight-edge ceiling, public records, and replay.
- `test_python_parser_links_only_bounded_straight_line_function_local_result_flow`,
  `test_python_parser_abstains_from_parameterized_branched_mutated_nested_or_deep_local_flow`, and
  `test_exact_function_local_result_flow_reaches_partial_claim_lineage` verify the zero-parameter
  straight-line local renderer, whole-function abstention boundaries, parser/cache versioning,
  partial Claim lineage, zero Findings, and model-free replay.
- `test_python_parser_links_one_exact_result_through_one_parameter_renderer_call`,
  `test_python_parser_abstains_from_unbound_ambiguous_or_mutated_parameter_renderer`, and
  `test_exact_parameter_renderer_call_reaches_partial_claim_lineage_without_execution` verify the
  unique positional call binding, its closed negative matrix, parser/cache versioning, partial
  Claim lineage, absence of project execution, zero Findings, and model-free replay.
- `test_python_parser_links_one_result_plus_exact_literal_renderer_arguments`,
  `test_python_parser_abstains_from_nonliteral_or_ambiguous_renderer_arguments`, and
  `test_result_plus_literal_renderer_reaches_partial_lineage_without_execution` verify the
  exact one-result-plus-literal-arguments profile, closed negative matrix, parser/cache version,
  model-free replay, missing project execution, and zero Findings.
- `test_python_parser_resolves_one_exact_literal_renderer_output_path`,
  `test_python_parser_abstains_from_dynamic_unsafe_or_unbound_renderer_output_paths`, and
  `test_literal_renderer_output_path_reaches_partial_lineage_without_execution` verify exact
  call-bound output Artifact identity, traversal/dynamic-path abstention, parser/cache version,
  replay, partial Claim lineage, and absence of execution or Findings.
- `test_python_parser_binds_exact_renderer_keywords_to_required_parameters`,
  `test_python_parser_rejects_inexact_renderer_keyword_binding`, and
  `test_keyword_renderer_binding_reaches_partial_lineage_without_execution` verify exact
  positional/keyword binding, missing/extra/duplicate/positional-only/unpacking/dynamic abstention,
  path and result linkage, parser/cache version, replay, and absence of execution or Findings.
- `test_python_parser_links_one_direct_unique_static_formatter_call`,
  `test_python_parser_rejects_ambiguous_or_opaque_static_formatter_flow`, and
  `test_direct_static_formatter_reaches_partial_lineage_without_execution` verify the exact
  single-return formatter, ambiguity/opacity/use-before-definition abstention, explicit flow basis,
  parser/cache version, replay, partial Claim lineage, and absence of execution or Findings.
- `test_python_parser_links_one_static_formatter_assignment_to_one_writer`,
  `test_python_parser_rejects_mutated_reused_or_indirect_static_formatter_assignment`, and
  `test_single_static_formatter_assignment_reaches_partial_lineage_without_execution` verify the
  one-binding/one-load/one-writer contract, order and mutation abstention, explicit flow basis,
  parser/cache version, replay, partial Claim lineage, and absence of execution or Findings.
- `test_python_parser_links_one_linear_static_formatter_assignment_chain`,
  `test_python_parser_rejects_non_linear_or_over_limit_static_formatter_chain`, and
  `test_static_formatter_assignment_chain_reaches_partial_lineage_without_execution` verify the
  linear-chain contract, fork/merge/rebinding/depth abstention, explicit flow basis, parser/cache
  version, replay, partial Claim lineage, and absence of execution or Findings.
- `scripts/verify_handoff.py` exercises the profile through the installed CLI and linked semantic
  segments.

## Remaining limitation

Accepted schema v0.8.0 represents the six grades independently, but this experiment cannot promote
the Claim to complete lineage because project execution and claim-specific report generation remain
unobserved. Alias chains longer than eight edges, formatter-flow branches or DAGs, renderers with
defaulted, keyword-only, variadic, unpacked, dynamic, or transformed output-path parameters,
multiple/conditional calls, branch-sensitive flow, multi-statement or multi-assignment formatter
returns, other cross-function returns, other computation shapes, other render APIs, and
qualitative diagnostic linkage remain unsupported.
Generalizing the profile or exposing a qualified detector requires a separate accepted decision
and qualification evidence.
