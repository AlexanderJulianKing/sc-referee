# Pseudoreplication recall slice: build-ready design

- Date: 2026-08-21
- Status: Design for review; no implementation authority by itself
- Decision source: Alex, relayed by Fable in this session on 2026-08-21 at approximately 14:20 America/Los_Angeles
- Target: one report-text-plus-full-CSV Finding lane for row-wise two-sample `ttest_ind`
- Fresh blind acceptance bar: 3/3 planted positives, 0/3 planted negatives, and zero false Findings on every required existing case
- Companion decision draft: `docs/implementation/ADR-0076-CONTRACT-BOUND-REPORT-CSV-PSEUDOREPLICATION-FINDING.md`

## 1. Decision boundary

This design implements one narrow claim:

> The exact selected report says that every row of one exact selected CSV entered a two-sample
> `scipy.stats.ttest_ind`-family test as one observation; the CSV contains repeated values in the
> human-authorized independent-unit column; the stated test N equals the complete CSV row domain;
> and every closed suppressor below completed without counterevidence.

It does not infer an independent unit from a header, repository prose, or repetition. It does not
prove that source code ran. It does not cover binomial tests, paired tests, regression, arbitrary
two-sample prose, AST-only pseudoreplication, H5AD, notebooks, or a general pseudoreplication class.
Any unsupported or ambiguous premise abstains.

Alex selected this lane instead of the multiple-testing promotion, set the fresh blind positive bar
to `N = 3`, required zero false Findings across the 108 blind cases, 155 regression cases, and all
new negatives, and directed that the existing scientific-requirement contract be extended without a
new authority record type or CLI flag. Those are supplied decisions, not conclusions inferred from
the repository.

The repository observations underlying the design are:

- The normal CLI already accepts a scientist profile through `method-contract`, and later accepts
  `--report`, `--material-input`, and `--method-contract-lock` through `audit`
  (`src/sc_referee/cli.py:632-679`, `:682-734`).
- The current requirement profile is the exact four-key
  `scientific_check_requirement_v1`/`1.0.0` shape
  (`src/sc_referee/scientific_requirement_contract.py:23-24`, `:86-136`).
- The frozen inspection context already carries exact, intake-selected material bytes and refuses a
  material input without a regular-file record and full-digest identity
  (`src/sc_referee/scientific_checks/core.py:61-94`, `:485-554`;
  `src/sc_referee/scientific_checks/integration.py:177-261`).
- The installed dependence check already names the semantic roles
  `authorized_independent_unit_key`, `analyzed_row_domain`, `row_independent_procedure`, and
  `selected_result_sink`, plus the required one-row and observed-multiple-row operands
  (`src/sc_referee/scientific_checks/dependence_recognition_adapter.py:42-65`).
- The normal controller evaluates scientific adapters before it binds the method contract
  (`src/sc_referee/controller.py:1128-1148`, `:1215-1233`). A verified authority projection must
  therefore be made available to inspection before adapter evaluation and then verified again by the
  existing final binding step. This ordering requirement is observed; the projection design below is
  new.
- The dependence Finding is currently admitted only through one exact installed pin and the generic
  method-conflict promotion/admission route
  (`src/sc_referee/detectors/method_conflict_grant_pins.py:43-88`;
  `src/sc_referee/controller.py:3530-3594`).

## 2. Reuse and new work

### Reused unchanged in meaning

- Check ID:
  `check:authorized-independent-unit-entry-into-row-independent-procedure`.
- Requirement candidate:
  `one-analyzed-row-per-authorized-independent-unit`.
- Requirement operand:
  `one_analyzed_row_per_authorized_independent_unit`.
- Conflict operand:
  `multiple_analyzed_rows_per_authorized_independent_unit`.
- Scientific-contract dimension: `dependence_structure`.
- Comparison form: `value_equals`.
- The four semantic role names listed above.
- The selected-publication-surface join, full-digest material-input representation, scientific-check
  compiler, post-hoc method ledger, generic bounded method-conflict detector, qualification resolver,
  Finding admission gate, emergency fail-closed behavior, and one binding ID:
  `method-conflict-binding:authorized-independent-unit-entry-into-row-independent-procedure-v1`.
- The existing `_DEPENDENCE_PIN` slot in the closed `GRANT_PINS` table. There will not be a second
  dependence pin or a sibling binding for the same check.

### New or versioned

- Requirement-profile schema `1.1.0`, carrying exact semantic-role authority.
- A method-contract material snapshot for the authority-named CSV.
- A pre-inspection, verified projection of existing Answer/assertion records into
  `FrozenInspectionContext.shared_derivations`; this is an internal frozen view, not a new public
  record type.
- One report/CSV adapter and one closed recognition grammar.
- One exact typed row-entry evidence projection carried by the normalized observation and copied to
  the reported semantic assertion.
- Dependence check version `1.2.0` and a new adapter identity.
- A dependence-specific bounded Finding wording profile and digest.
- Fresh qualification evidence, metric set, threshold policy, and re-derived contents of the
  existing dependence pin after the blind envelope passes.

### Retained only as history or development evidence

The current `1.1.0` static-certificate adapter, its hidden
`dependence_authorization_lock` controller arguments, and the old dependence qualification remain in
the tree and retained evidence, but they are not inputs to this lane. The active `1.2.0` dependence
module replaces the old adapter rather than requiring both `static_source` and `reported_text` planes.
Keeping both active would make the generic binding require both planes and would defeat the selected
report-plus-CSV scope. This replacement is a proposed decision, not an observed property of the code.

The existing pin cannot be copied byte-for-byte: it pins the old check version, binding digest,
adapter implementation, adapter manifest, grammar, qualification, metric set, and two-root threshold
(`src/sc_referee/detectors/method_conflict_grant_pins.py:43-88`). “Reuse the pin” therefore means
reuse its binding ID, its one closed registry slot, and its resolver/admission mechanics; every
identity changed by this envelope must be re-derived and reviewed. The old pin remains active until
the new blind evidence passes and the replacement is installed in one reviewed change.

## 3. Exact scientific-requirement contract extension

### 3.1 Versioning and compatibility

The profile ID stays `scientific_check_requirement_v1`. Its current-creation schema version becomes
`1.1.0`; this is the requested schema-version bump. Version `1.0.0` locks remain replayable under
their old meanings. They may bind to a later audit only while their frozen check manifest still
matches the active registry; in particular, an old dependence lock cannot bind to the new `1.2.0`
check. They carry no unit-key authority and are ineligible for the new report/CSV dependence Finding.

The public record schema remains `0.19.0`. No public JSON Schema fork is needed because Answer
`answer_value` is deliberately unconstrained and `extensions` admits `x-` properties
(`src/sc_referee/resources/schemas-v0.19.0/schemas/v0.19.0/answer.schema.json:95-167`). The ADR is still
required because this changes authority and Finding eligibility, exactly the change class named in
`AGENTS.md:56-58`.

For a newly created `1.1.0` profile, the top-level object must contain exactly these five fields:

| Field | Type | Exact constraint |
| --- | --- | --- |
| `profile_id` | string literal | `scientific_check_requirement_v1` |
| `profile_version` | string literal | `1.1.0` |
| `check_id` | nonempty string | Must resolve to exactly one installed check. |
| `candidate_id` | nonempty string | Must resolve to exactly one candidate of that check. |
| `semantic_role_authority` | object | Closed shape below; no other keys. |

For this dependence check/candidate, `semantic_role_authority` must equal an object with exactly one
member, `authorized_independent_unit_key`. Its value must contain exactly:

| Field | Type | Exact constraint |
| --- | --- | --- |
| `material_input_path` | string | Normalized repository-relative POSIX path of at most 512 ASCII characters; every segment must match `[A-Za-z0-9][A-Za-z0-9._-]*`; suffix exactly `.csv` case-insensitively. |
| `column_name` | string | Must match `[A-Za-z][A-Za-z0-9_.-]{0,127}` exactly; comparison to the decoded CSV header is byte-exact, with no case folding or Unicode normalization. |
| `group_contrast_column` | string | Must match the same exact column-name regex, differ byte-exactly from `column_name`, and identify the human-authorized two-group contrast column; it is never inferred from a header, report, or group labels. |

For all other installed checks under profile `1.1.0`, `semantic_role_authority` must be exactly `{}`.
The builder must not add generic arbitrary role objects, infer missing values, accept aliases such as
`unit`, `sample_id`, or `donor`, or read the value from project prose.

### 3.2 Complete e9e2718 profile record

This is the complete human-supplied profile record for the retrospective e9e2718 development case:

```json
{
  "profile_id": "scientific_check_requirement_v1",
  "profile_version": "1.1.0",
  "check_id": "check:authorized-independent-unit-entry-into-row-independent-procedure",
  "candidate_id": "one-analyzed-row-per-authorized-independent-unit",
  "semantic_role_authority": {
    "authorized_independent_unit_key": {
      "material_input_path": "data/input.csv",
      "column_name": "colony_id",
      "group_contrast_column": "reef_zone"
    }
  }
}
```

The case itself states `colony_id` as the independent-unit column
(`evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/e9e2718573bb47f7d17b/data-description.md:12-20`),
and its report names `data/input.csv` in the accepted row-entry statement
(`evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/e9e2718573bb47f7d17b/results/report.md:5-8`).
Those project files are retrospective development evidence; in production the human profile above,
not the prose, supplies authority.

`method-contract` must force `data/input.csv` into its material full-digest set before it emits the
lock. For this exact file, the deterministic locked projection is:

```json
{
  "authorized_independent_unit_key": {
    "material_input_path": "data/input.csv",
    "column_name": "colony_id",
    "group_contrast_column": "reef_zone",
    "material_input_content_digest": "sha256:e8a99506dacf5fc7ebd71f578d07267afd48a231310d88cf28d6330e27dab19b"
  }
}
```

That projection is stored as `profile_manifest.authority_binding_snapshot`; it is controller-derived,
not a second scientist claim.

### 3.3 Exact record propagation

`ResolvedScientificRequirement` gains `profile_version`, `semantic_role_authority`, and
`authority_binding_snapshot`. The latter is empty until `run_method_contract` resolves the named
regular file to one full-digest identity. These values participate in the profile-manifest digest,
contract/Answer/assertion stable IDs, and semantic-lock digest.

For profile `1.1.0`, the parent Answer must have exactly this `answer_value` shape:

```json
{
  "dependence_structure": "one_analyzed_row_per_authorized_independent_unit",
  "semantic_role_authority": {
    "authorized_independent_unit_key": {
      "material_input_path": "data/input.csv",
      "column_name": "colony_id",
      "group_contrast_column": "reef_zone"
    }
  }
}
```

The parent human declaration and controller-verified assertion copy the human object under
`extensions.x-semantic-role-authority`; the verified assertion also copies the controller-derived
snapshot under `extensions.x-authority-binding-snapshot`. The existing Answer digest covers the new
`answer_value`, and the existing profile-manifest and semantic-lock digests cover both extensions.
The audit-bound Answer and `verified_intended_dependence_structure` assertion copy the same two
objects only after the parent Answer digest, parent lock, unchanged task, active check/candidate, and
current material path/digest all agree.

The existing Answer remains the authority record. No `human_method_authorization` record, custom
unit-authority record, or audit CLI option is introduced.

### 3.4 Pre-inspection authority projection

Before `active_scientific_checks.evaluate`, the controller performs a read-only preflight only when
the supplied method-contract lock is a resolved `1.1.0` profile for this exact check/candidate:

1. Verify the method-contract envelope and semantic-lock digest.
2. Verify the parent ScientificContract, one human Answer, declaration/derivation pair, Answer digest,
   and profile manifest using the existing verifier.
3. Verify that the governing task has the same full digest in the current snapshot.
4. Verify that `authority_binding_snapshot` identifies exactly one parent regular file and that the
   current audit selected exactly one material input whose path and content digest match it.
5. Freeze the already-existing parent Answer and verified semantic assertion into
   `FrozenInspectionContext.shared_derivations`.

The report/CSV adapter accepts authority only from that exact pair. Final
`bind_frozen_method_contract` repeats the complete verification and binds the requirement to the one
question produced by the adapter. Preflight/final disagreement, duplicate authority, material drift,
or any malformed projection yields no Finding. Integrity drift in the supplied lock or frozen input
is a fail-closed audit error; absence of an otherwise valid in-scope authority is an adapter abstention.

## 4. Closed report/CSV recognition grammar

### 4.1 Identities

- Check version: `1.2.0`.
- Adapter ID:
  `adapter:authorized-independent-unit-entry-into-row-independent-procedure:report-csv-rowwise-ttest-v1`.
- Adapter version: `1.0.0`.
- Evidence plane: `reported_text`.
- Parser identity: selected Markdown report through
  `parser:markdown-inventory` version `0.2.0`, state exactly `parsed`.
- Applicability profile: `bounded-report-csv-rowwise-ttest-dependence-v1`.
- Output ceiling before qualification: `question_only`.
- Project-authored-code execution: `false`.

The active module contains this adapter alone. The method-conflict binding therefore requires exactly
`reported_text` and assertion role `reported`. All four existing dependence semantic roles remain
required.

### 4.2 CSV grammar and bounds

The adapter accepts exactly one authority-named and CLI-selected `.csv` input. It decodes strict UTF-8
without BOM, rejects NUL and noncanonical CR-only newlines, and parses with Python's controller-owned
`csv.reader` using the `excel` dialect, `strict=True`, and `newline=""`. This is a static data read,
not execution of project code.

The accepted table has:

- one nonempty header row and 2 through 100,000 data rows;
- 1 through 512 columns;
- a maximum decoded field length of 1 MiB and the existing material-input byte budgets;
- nonempty, unique headers, each identical to its stripped form;
- every data row exactly the header width;
- exactly one header byte-equal to the authorized `column_name`;
- every unit value nonempty and identical to its stripped form; and
- at least two distinct unit values.

The selected report path must obey the same safe ASCII segment grammar and end in `.md` or `.markdown`.
These path/header bounds are part of Finding-wording safety as well as recognition; an otherwise valid
project outside them abstains.

Let `N_csv` be the complete data-row count, `U` the number of distinct exact unit values, `R` the
number of distinct unit values with multiplicity greater than one, and `M` the maximum multiplicity.
`N_csv > U`, `R >= 1`, and `M >= 2` are required for the conflict operand. `N_csv == U` is a covered
negative. Any malformed, truncated, oversized, duplicate-header, missing-unit, or ambiguous table
abstains.

Before any composite-key uniqueness test, the adapter constructs candidate columns `C` without type
inference over the complete row domain. A column is a candidate if and only if it is neither the
authorized unit column nor the contract-authorized `group_contrast_column`, and its complete-domain
distinct-value count is at most `U`. Columns with distinct count greater than `U` are excluded before
uniqueness is tested. The group/contrast column is authority and is never inferred from a header,
report wording, or table labels.

For each candidate `C` and each distinct authorized unit value `u`, compute `T_C(u)`, the ascending byte-lexicographic
sort of the complete tuple of decoded `C` values on rows whose authorized unit equals `u`; duplicates and
empty strings remain in the tuple. `C` is a **within-unit index** if and only if every `T_C(u)` is
byte-for-byte identical, including tuple length, order after sorting, and every value. The empty set of
units is impossible under the accepted CSV grammar and cannot vacuously satisfy this definition.

For each candidate `C`, also compute whether all ordered byte-exact pairs `(authorized_unit_value, C_value)` are
unique across the `N_csv` rows. The adapter abstains with
`unique-nonindex-authorized-unit-composite-key-possible` if and only if at least one `C` has unique pairs
and is not a within-unit index. A unique-pair column that is a within-unit index does not suppress.
Failure to complete candidate selection for every column or every candidate tuple and uniqueness scan
abstains. There is no additional header, type, response-variable, or identifier inference or exemption.

Consequences on the four K t-test CSVs are fixed:

- 0de3 (`U=10`): `plot_id` and contract group `management` are excluded by role; `water_table_cm`
  (`28` distinct) and `ch4_flux_mg_m2_h` (`40`) are excluded because distinct count exceeds `U`;
  `visit` (`4`) is the sole candidate, is a within-unit index, and does not suppress.
- 6b2da (`U=10`): `reactor_id` and contract group `carbon_source` are excluded by role;
  `nitrate_removal_mg_n_per_l_per_h` (`59`) is excluded because distinct count exceeds `U`; `run_day`
  (`6`) is the sole candidate, is a within-unit index, and does not suppress.
- e9e2718 (`U=12`): `colony_id` and contract group `reef_zone` are excluded by role; `nubbin_code`
  (`48`) and `symbiont_density_e6_per_cm2` (`44`) are excluded because distinct count exceeds `U`;
  `depth_m` (`12`) is the sole candidate, is not a within-unit index, but its `(colony_id, depth_m)`
  pairs repeat within colonies and are not unique, so it does not suppress.
- 3ae92 (`U=12`): `plot_id` and contract group `water_table_regime` are excluded by role;
  `chamber_temp_c` and `ch4_flux_mg_m2_h` (each `60`) are excluded because distinct count exceeds `U`;
  `survey_round` (`5`) is the sole candidate, is a within-unit index, and does not suppress.

The closed label-collision control has authorized unit `colony`, a separate contract group column,
and rows `(colony=A, site=north)`, `(A, south)`, and `(B, north)`. Because
`distinct(site)=2 <= U=2`, `site` is a candidate.
Its three `(unit, site)` pairs are unique, while the sorted site tuples are `(north, south)` for `A`
and `(north)` for `B`; `site` is not a within-unit index, so the adapter abstains. A balanced collision
with identical site tuples is not detected by this rule and remains a declared coverage limit.

### 4.3 Accepted test spellings

The following definitions are normative for every report match and suppressor in this design:

- **Visible text.** The adapter accepts text only from parser-recognized ATX-heading labels,
  paragraphs, list-item paragraphs, and individual GitHub-Flavored-Markdown table cells. Emphasis and
  strong-emphasis delimiters are removed while their text remains. Backtick inline-code delimiters are
  removed and their literal code content remains, so `` `data/input.csv` `` exposes
  `data/input.csv`. Link-label text remains; link destinations and titles do not. Image destinations,
  image alt text, HTML, fenced/indented code, and block quotes supply no visible text and cannot supply
  evidence. Table cells remain separate blocks; a phrase or proximity window cannot cross a cell
  boundary. Parser failure or inability to classify any evidence-bearing construct abstains.
- **Whitespace-normalized.** Within one visible-text block, replace each maximal ASCII whitespace run
  matching `[ \t\r\n\f\v]+` with one U+0020 space and remove leading/trailing U+0020. No punctuation,
  backtick content, table-cell boundary, or non-ASCII whitespace is rewritten. Matching then performs
  ASCII-only case folding (`A`-`Z` to `a`-`z`). A would-be match containing unclassified non-ASCII
  whitespace does not match.
- **Report token.** After whitespace normalization and ASCII folding, a token is one maximal
  `[a-z0-9]+` run. Punctuation and hyphens are boundaries. Token-sequence matches cannot cross visible
  blocks or table cells.
- **Glob boundary.** A one-token glob such as `aggregat*`, `collapse*`, `pool*`, `permut*`, or
  `resampl*` matches only a complete report token whose prefix is exactly the text before `*`; `*`
  consumes only the remainder of that token. A two-token glob such as `matched pair*`,
  `mixed effect*`, or `random effect*` requires consecutive tokens: the first is exact and the second has
  the stated prefix.
  Thus exact token `sum` does not match `summary` or `summarised`, and `aggregat*` also does not match
  either word.
- **Authorized-unit stem.** ASCII-fold `column_name`, split it on one or more `_`, `.`, or `-`
  characters, and, if present, remove one final token exactly equal to `id`, `ids`, `identifier`,
  `identifiers`, `code`, `codes`, `key`, or `keys`. The remaining nonempty tokens are the complete stem
  set and match only complete report tokens; there is no singularization or linguistic stemming. For
  example, `plot_id` yields only `plot`, while `sampling.site-id` yields `sampling` and `site`.
- **Fixed unit nouns.** The complete non-authority list is `unit`, `subject`, `donor`, `patient`,
  `animal`, `plot`, `colony`, `reactor`, `cage`, `well`, `site`, `litter`, `participant`, `cluster`,
  `mouse`, and `tank`. An unlisted prose noun cannot serve as positive unit evidence. If a suppressor
  decision would require deciding whether an unlisted noun denotes the unit, the adapter abstains.
- **Report-wide method class and join.** Enumerate every accepted test-spelling occurrence anywhere in
  visible report text. Every non-neutral occurrence must normalize to exactly one Student-versus-Welch
  class across the whole report; a Student/Welch class conflict abstains. Any number of neutral
  `scipy.stats.ttest_ind` occurrences may coexist with that one class, and an all-neutral report is
  permitted. Each occurrence is an ordinary `method` node with role rank 0. The minimal-join algorithm in
  section 4.5 chooses the report-wide occurrence that minimizes the complete join key while retaining the
  unchanged 16-line adjacent-gap, per-adjacent-pair heading, and 40-line envelope bounds. The selected
  result block need not itself contain a test spelling. Exactly one normalized t/p result node is still
  required under section 4.6; a second conflicting result abstains.
- **Finite decimal literal.** `DEC` is the full token regex
  `[+-]?(?:(?:0|[1-9][0-9]*)(?:\.[0-9]+)?|\.[0-9]+)`. It is at most 64 ASCII characters and must parse
  as a finite `decimal.Decimal`; `NaN`, infinities, exponent notation, and an integer with a leading
  zero are excluded. `<DF>` and `<P>` additionally must be nonnegative; `<T>` may be signed.
- **Scientific-notation literal.** `SCI` is the full token regex
  `[+-]?(?:(?:0|[1-9][0-9]*)(?:\.[0-9]+)?|\.[0-9]+)[eE][+-]?(?:0|[1-9][0-9]*)`, is at most 64 ASCII
  characters, and must parse as a finite `decimal.Decimal`. `<P>` must be nonnegative. Every numeric
  match has left boundary `(?<![A-Za-z0-9_.])` and right boundary
  `(?![A-Za-z0-9_])(?!\.[0-9])`. Thus a sentence-final period after `<P>` is permitted, but a continuation
  such as `0.0001.5` is not lexed as `0.0001`.

Hyphen and space are not generally interchangeable; the following are the complete accepted test
spellings after the normalization above:

- `two-sample Student t-test`;
- `two-sample Student t test`;
- `Welch's two-sample t-test`;
- `Welch's two-sample t test`; and
- `scipy.stats.ttest_ind`.

One block may contain more than one accepted spelling, as in “Welch's two-sample t-test
(`scipy.stats.ttest_ind`, `equal_var=False`)”, and the method occurrence selected for the join may be in
a different block from the one t/p result. Any report-wide combination of Student/pooled and
Welch/unequal-variance declarations abstains. Both accepted Student and Welch forms normalize to the
single procedure fact
`scipy.stats.ttest_ind_two_sample`, because both treat their supplied rows as independent within
groups for this predicate.

`independent-samples t-test` and `two independent groups` are not accepted test or row-entry forms.
They can describe independence between the two comparison groups without saying that repeated rows
within one authorized unit entered as independent observations. Accepting either would open the exact
false-accusation route this slice is designed to avoid.

### 4.4 Accepted row-entry admissions

Exactly one whitespace-normalized match family must occur in the joined target block. The complete
list is:

1. `PATH_ANCHOR(<SELECTED_PATH>)` joined to
   `each of the <N> measurement rows entered the test as one observation`;
2. `PATH_ANCHOR(<SELECTED_PATH>)` joined to
   `each sampling-day measurement in the file was entered as one observation`;
3. `every nubbin record in <SELECTED_PATH> contributed one observation to the test`; and
4. `PATH_ANCHOR(<SELECTED_PATH>)` joined to
   `<TTEST_NAME> on the <N> individual chamber readings`.

`<N>` is an unsigned base-10 integer without comma, decimal point, sign, exponent, or leading zero and
must be at least 2. `<SELECTED_PATH>` must be byte-identical to the authority and CLI-selected CSV path.
`<TTEST_NAME>` must be one of the accepted spellings above. No synonym, stemming, semantic paraphrase,
model judgment, or bare form such as `N observations were analyzed` may satisfy this check. The bare
form is insufficient because those observations may already be independent-unit aggregates.

`PATH_ANCHOR(<SELECTED_PATH>)` is exactly one of these normalized substrings in one visible paragraph,
list-item paragraph, or table cell:

- `source file: <SELECTED_PATH>`; or
- `the file <SELECTED_PATH> records`.

The selected-path bytes may originate in inline code because inline-code contents are visible text.
There must be exactly one accepted selected-path anchor and no other visible `.csv` path in the report.
Path comparison is byte-identical after visible-text extraction and whitespace normalization; report
ASCII folding is not applied to path bytes. A visible CSV token uses left boundary
`(?<![A-Za-z0-9._/-])` and right boundary `(?![A-Za-z0-9_/-])(?!\.[A-Za-z0-9_/-])`; this recognizes a
CSV path followed by sentence punctuation while refusing a longer suffix such as `.csv.bak`.
For forms 1, 2, and 4, the compound admission node is the inclusive physical-line interval from that
anchor through the admission phrase; the two components must be at most 16 complete intervening lines
apart with at most one ATX heading strictly between them. Form 3 binds the path directly and needs no
anchor. A pathless phrase, `the file` without its unique antecedent, a mismatched path, an ambiguous
antecedent, or inability to scan the full report for another `.csv` path abstains.

### 4.5 N witnesses and the bounded two-span join

`N_report` is chosen from a closed set:

- the `<N>` slot of admission form 1 or 4;
- the exact literal form `measurement rows analysed: <N>` or
  `measurement rows analyzed: <N>`;
- `<TTEST_NAME> on the <N> measurement rows`; or
- the arithmetic sum of exactly two positive integer cells in one Markdown table column headed
  exactly `n`, `rows`, `measurements`, or `measurement rows` after ASCII case folding.

For a two-row table witness, the table must have exactly two body rows, two distinct nonempty group
labels in its first column, and one accepted N column. Both group labels must also occur as whole
visible-text tokens in the joined test/result block. The builder performs integer addition only; it
does not infer a group column from the CSV.

For a table headed `measurements` or `measurement rows`, the report-wide suppressor scan must include
the full table, every parser-recognized caption node attached to it, and the entire nearest preceding
paragraph or list-item block in the same ATX section, if one exists. Zero such caption/introducing
blocks is a determinate result; inability to determine or scan them abstains. This prevents an explicit
pre-aggregation explanation around a superficially row-like table from being omitted from the
suppressor domain.

Every qualifying N witness in the joined target block must equal `N_csv`. Equal corroborating totals
and a table whose two counts sum to the same total are allowed; an unequal count, a third group row, a
second candidate table for another test, or a count that cannot be assigned uniquely abstains. The
witness preference is deterministic: an N inside the accepted admission, then an N in the same
paragraph, then the smallest physical-line gap; physical start byte, end byte, and normalized match
bytes break any remaining tie.

“Minimal join” means this deterministic algorithm:

1. Enumerate every qualifying node for the canonical roles `method`, `admission`, `N witness`,
   `group labels`, and `result`, recording report digest, start/end physical line, start/end byte,
   normalized matched bytes, and match-family ID. The compound path-bound admission in section 4.4 is
   one admission node.
2. Enumerate each base tuple containing exactly one report-wide `method`, `admission`, `N witness`, and
   `result` node and satisfying the path, report-wide method-class, N, result, and no-conflict conditions. Its base envelope is
   the inclusive minimum-start through maximum-end physical-line interval. If the selected N witness is
   a two-group table, its group-label node is mandatory. Otherwise, any qualifying two-group table N
   witness wholly inside the base envelope is a corroborating witness and its group-label node is also
   mandatory; more than one such table abstains. If neither condition applies, the group-label role is
   omitted. A node may fulfill more than one role; its role-specific entries then have identical
   coordinates.
3. For each tuple, sort its role entries into the ordered node list by
   `(start_line, start_byte, end_line, end_byte, role_rank, match_family_id)`, where role ranks are
   `method=0`, `admission=1`, `N witness=2`, `group labels=3`, and `result=4`.
4. For each adjacent pair in that ordered list, an overlap has gap zero; otherwise the gap is the number
   of complete physical lines strictly between the earlier end and later start. Reject the tuple if any
   gap exceeds 16, or if **that adjacent-pair interval** contains more than one Markdown ATX heading.
   Also reject the tuple if its total inclusive envelope from the first ordered node's start line through
   the last ordered node's end line exceeds 40 physical lines. There is no whole-envelope ATX-heading
   count cap. Reject an intervening conflicting test, unequal N, different group table, or
   incompatible result.
5. Among surviving tuples choose the lexicographically least key
   `(envelope_line_count, sum_of_adjacent_gaps, maximum_adjacent_gap,
   ordered_node_coordinate_and_role_sequence, ordered_normalized_match_sequence)`. This tuple and only
   this tuple is the minimal join. Duplicate parser nodes with the same complete key but different
   source bytes are malformed and cause abstention; no semantic tie-break is permitted.

Fenced/indented code blocks, block quotes, raw HTML blocks, link destinations used as evidence,
malformed tables, or a Markdown parser state other than `parsed` make the composition unsupported.

### 4.6 Inferential result witness

At least one result block in the bounded join must contain both:

- `t(<DF>) = <T>`, `t = <T>`, or `Welch t = <T>` (the t and optional df tokens are finite decimal
  literals); and
- `p < <P>`, `p <= <P>`, `p = <P>`, `p >= <P>`, or `p > <P>`, where P is a finite decimal literal or
  base-10 scientific-notation literal.

The t and p spans may be on separate adjacent Markdown list lines with at most four physical lines
between them and no intervening heading. Multiple result statements are allowed only when their
normalized t and p comparator/value facts agree exactly; any disagreement or second test abstains.
The selected report Artifact, not an answer-key marker or filename convention, supplies the
`selected_result_sink` role.

## 5. Complete ordered Finding predicate

The builder must implement these checks in order. A later check may not repair, infer, or weaken a
failed earlier check.

1. **Exact envelope selection.** Consume the requested check ID, candidate ID, and profile version.
   Require the exact IDs in sections 2 and 3 and `1.1.0`. Otherwise this adapter is not applicable.
2. **Parent authority integrity.** Consume the frozen Answer, verified assertion, profile manifest,
   Answer digest, actor, governing-task SourceRef, and parent semantic-lock digest. Require one human
   Answer and one exact verified derivation with the section 3 shapes. Missing, duplicate, post-hoc,
   agent-authored, malformed, or digest-mismatched authority abstains or fails lock validation; it can
   never convict.
3. **Exact frozen material.** Consume `authority_binding_snapshot`, current repository/file/asset
   records, `FrozenMaterialInput`, and selection proof. Require exactly one selected material input and
   exact equality of path and full digest to the parent snapshot. Drift or selection ambiguity blocks
   the Finding.
4. **Exact selected report.** Consume the publication surface, selected Artifact, full-digest identity,
   Markdown parser result, and report bytes. Require one `parsed` strict-UTF-8 Markdown report and the
   one-edge selected-publication join. Otherwise abstain.
5. **Complete CSV structure.** Consume the full selected CSV bytes. Apply every bound in section 4.2,
   inventory the complete row domain, and complete every authorized-unit/other-column composite scan.
   Any inability to complete the scan abstains.
6. **Authorized unit and composite-key relation.** Consume the exact authorized column name and parsed
   rows. Require the exact header, nonempty values, `N_csv > U`, `R >= 1`, and `M >= 2` and require that
   no D1' candidate column—excluding the authorized unit, the contract group/contrast, and every column
   with distinct count above `U`—both makes `(authorized unit, candidate column)` unique across all rows
   and is not a within-unit index under section 4.2. `N_csv == U` is a covered negative; a candidate
   unique-pair nonindex is a suppressor, a candidate unique-pair within-unit index is not, and all
   unresolved states abstain.
7. **Supported Markdown composition.** Consume Markdown block/line structure. Reject every unsupported
   composition in section 4.5 before lexical matching.
8. **Report-wide scientific suppressor scan.** Consume all visible report text, including every table
   cell and the caption/introducing-block domain defined in section 4.5, and apply the complete list in
   section 6. Any hit abstains regardless of grammatical negation; silence cannot be upgraded to
   evidence outside this exact report-declaration predicate.
9. **One row-independent procedure.** Consume visible prose spans. Require at least one accepted
   section 4.3 spelling, at most one report-wide non-neutral Student/Welch class, and one method occurrence
   that survives as the rank-0 node in the deterministic minimal join. Missing, class-conflicting, or
   competing procedures abstain; neutral spellings may coexist with the one non-neutral class.
10. **One literal path-bound row-entry admission.** Consume visible prose spans and the selected path.
    Require one of the four section 4.4 families, including the direct path in form 3 or the exact unique
    `PATH_ANCHOR` in forms 1, 2, and 4. Multiple nonidentical families, a missing/ambiguous anchor, another
    visible CSV path, a path mismatch, or a paraphrase abstains.
11. **Exact report N.** Consume admission, literal total, and Markdown table candidates. Resolve
    `N_report` under section 4.5 and require `N_report == N_csv`. No tolerance or approximate language is
    allowed.
12. **Bounded span join.** Consume all selected spans and physical lines. Construct the exact minimal
    join and enforce every 16-line/per-adjacent-pair-one-heading rule, the inclusive 40-line
    whole-envelope ceiling, group-label rule, tie-break, and no-intervening-conflict condition in
    section 4.5.
13. **Inferential result.** Consume result tokens. Require at least one exact t/p pair and exact agreement
    among duplicates under section 4.6.
14. **Selected sink closure.** Consume the scope-join graph. Require the report Artifact to be the unique
    selected publication surface. There is no source-writer or execution inference.
15. **Complete adapter receipts.** Consume checks 2 through 14. Emit an applicable observation only if
    every registered adapter receipt is present and passed. Any impossible receipt is `unsupported`,
    never “absent”.
16. **Typed observed operand.** Emit exactly
    `multiple_analyzed_rows_per_authorized_independent_unit`, evidence plane `reported_text`, the four
    reused roles, exact report spans, exact material SourceRef, and the row-entry fact projection in
    section 7. No other operand is permitted.
17. **Final contract binding.** Consume the parent lock again, active registry, current material identity,
    generated question, child Answer, and child verified intended assertion. Require one exact current
    binding and exact equality of authority projections. Otherwise no method-conflict target exists.
18. **Generic conflict and finite method checks.** Consume the generic post-hoc ledger and its ten
    registered checks. Require the intended one-row operand to differ from the reported multiple-row
    operand and require no alternate intent, amendment, approved deviation, applicability mismatch,
    sensitivity qualifier, ambiguity, or scope failure
    (`src/sc_referee/detectors/bounded_analysis_method_conflict.py:588-797`).
19. **Exact new qualification grant.** Consume the unchanged binding ID, new binding/check/adapter/grammar
    identities, new qualification and metric set, threshold-policy digest, and the installed pin. The old
    `1.1.0` qualification is not authority for this predicate.
20. **Wording-profile pin and admission.** Recompute the Finding from the exact row-entry facts, require
    the pinned wording-profile digest, resolved evidence refs, applicable qualification, complete
    counterevidence, deterministic input digest, and normal admission. Any mismatch returns the
    evaluation candidate and zero Findings.

Only all 20 checks may produce one Finding.

## 6. Full suppressor and abstention table

All lexical suppressors are scanned in the complete visible-report domain defined in sections 4.3 and
4.5 after whitespace normalization and ASCII folding. This includes every table cell, any attached
caption, and any determined table-introducing paragraph/list item, whether or not it belongs to the
minimal join. A lexical hit is not interpreted for polarity: “no mixed effects” still abstains because
this slice has no negation grammar. That is intentionally conservative. Accepted semantic-assertion
suppressors are evaluated by exact predicate/value, not by prose. An incomplete lexical, table-context,
CSV, or assertion scan always abstains.

| Suppressor or uncertainty | Static detection | Result when present or detection cannot complete |
| --- | --- | --- |
| Missing, duplicate, nonhuman, malformed, or wrong-scope authority | Exact parent Answer/assertion/profile/digest checks | Fail closed or abstain; never convict. |
| Material path/digest drift or more than one selected material input | Exact parent/current path, full digest, and selection-cardinality comparison | Fail closed or abstain. |
| CSV parse, budget, width, header, row-width, encoding, or missing-value uncertainty | Complete section 4.2 scan | Abstain. Partial rows are never evidence. |
| No repeated authorized unit | Exact multiplicity count | `N_csv == U`: covered negative; malformed/unknown: abstain. |
| Possible composite independent unit | Apply D1' candidate selection, then compute exact complete-domain pair uniqueness and byte-identical sorted within-unit tuples only for candidates as specified in section 4.2 | A candidate unique-pair `C` that is not a within-unit index abstains; a candidate unique-pair within-unit index does not. Any incomplete candidate or tuple scan abstains. |
| Report/parser/selection ambiguity | Exact Artifact, full digest, parser identity/state, and publication join | Abstain. |
| Unit-level aggregation or pseudobulk | Report-wide token `pseudobulk`; consecutive tokens `pseudo bulk`; token `aggregat*`; or an authorized-unit stem or fixed unit noun within four tokens of `mean`, `median`, exact token `sum`, `collapse*`, or `pool*` | Abstain, including negated mentions. Exact `sum` does not match `summary` or `summarised`; neither generic word is a hit by itself. |
| Paired, matched, blocked, or within-unit testing | Tokens `paired`, `matched pair*`, `within-subject`, `within-unit`, `within-donor`, `within-patient`, `within-plot`, `within-colony`, `ttest_rel`, or `blocked test` under section 4.3 boundaries | Abstain. |
| Experimental hierarchy or nesting | Consecutive tokens `split plot`, `sub plot`, or `whole plot` (therefore accepting hyphenated and spaced surface forms), or exact token `nested` | Abstain, including negated mentions. |
| Technical replication | Consecutive-token glob `technical replicate*` | Abstain, including negated mentions. |
| Mixed/random-effects modeling | Tokens `mixed effect*`, `mixed-effect*`, `random intercept`, `random slope`, `random effect*`, `lmer`, or `glmer` | Abstain. |
| Cluster-adjusted inference | Tokens `cluster-robust`, `cluster robust`, `clustered standard error*`, `GEE`, `generalized estimating equation*`, or `sandwich` within four tokens of `variance`, `standard error`, `SE`, or `estimator` | Abstain. |
| Repeated-measures/correlated model | Tokens `repeated measure*`, `correlated error*`, `correlation structure`, `exchangeable correlation`, `autoregressive correlation`, or `subject-level covariance` | Abstain. |
| Unit-level resampling/randomization | An authorized-unit stem or any fixed unit noun within four tokens of `bootstrap*`, `permut*`, `resampl*`, or `shuffle*`; or the exact consecutive tokens `randomized at` or `randomised at` (regex notation `randomi[sz]ed at`) | Abstain. An unlisted noun that would require semantic unit interpretation makes the scan unresolved and therefore abstains. |
| Sensitivity, secondary, exploratory, descriptive, or illustrative status | Tokens `sensitivity analysis`, `sensitivity-only`, `secondary analysis`, `exploratory`, `descriptive only`, `illustrative only`, or `not the primary analysis` | Abstain. |
| Approved method deviation | Accepted same-subject assertion predicate `approved_method_deviation`, or visible phrase `approved deviation` | Generic finite check suppresses; prose hit also abstains. |
| Governing protocol or plan revision | Accepted same-subject assertion predicate `governing_protocol_amendment`; visible consecutive tokens `protocol amendment`, `amended protocol`, `revised protocol`, `revised analysis plan`, or `revised sap` | Generic finite check suppresses; any prose hit also abstains. |
| Conditional inapplicability | Accepted `method_obligation_applicability` object other than `applies` | Generic finite check suppresses. Missing exact resolution abstains. |
| Competing procedure | Report-wide tokens for another inferential family: `paired t-test`, `ttest_rel`, `ANOVA`, `regression`, `Mann-Whitney`, `Wilcoxon`, `chi-square`, `Fisher's exact`, `binomtest`, or `permutation test`, plus any report-wide Student/Welch accepted-spelling class conflict | Abstain. Ordinary prose use of “model” alone is not a hit. |
| Ambiguous or conflicting N | Any qualifying total/table not equal to `N_csv`, third table group, unresolved tie, approximate N, or unmatched group labels | Abstain. |
| Multiple or conflicting results | A second t/p fact pair with different normalized values, or a second procedure/result join | Abstain. Equal restatements are allowed. |
| Unsupported report composition | Fenced/indented code, block quote, raw HTML, malformed Markdown table, evidence only in a link target, more than one ATX heading in any adjacent-node interval, an adjacent gap above 16, or a total envelope above 40 lines | Abstain. There is no whole-envelope heading-count cap. |
| Bare group-independence wording | `independent-samples t-test`, `two independent groups`, or bare `N observations were analyzed` without an accepted admission | Not applicable or unsupported; never convict. |
| Unsupported scientific surface | Binomial test, R-only procedure, H5AD, notebook output, AST-only route, non-CSV table, or any unlisted spelling/template | Not applicable when no in-scope trigger exists; otherwise unsupported. Never convict. |
| Evidence or verifier exception | Decode, parser, arithmetic, memory-budget, schema, or adapter exception | Localized unsupported result. No Finding and no fallback matcher. |

## 7. Typed row-entry fact and bounded Finding wording

The normalized observation gains one optional, exact internal projection named
`row_entry_evidence`. Existing observations omit it and retain byte-identical serialization. Its only
initial profile is `report_csv_row_entry_evidence_v1`, with these required fields and no extras:

- `material_input_path: str`
- `material_input_content_digest: Digest`
- `material_file_ref: RecordRef(file_record)`
- `authorized_unit_column: str`
- `group_contrast_column: str`
- `data_row_count: int`
- `distinct_unit_count: int`
- `repeated_unit_count: int`
- `maximum_unit_multiplicity: int`
- `composite_key_scan_complete: Literal[true]`
- `composite_key_candidate_columns: sorted array[str]`
- `distinct_count_excluded_columns: sorted array[str]`
- `within_unit_index_columns: sorted array[str]`
- `unique_pair_within_unit_index_columns: sorted array[str]`
- `unique_nonindex_authorized_unit_composite_columns: Literal[[]]`
- `report_path: str`
- `report_content_digest: Digest`
- `procedure_id: Literal["scipy.stats.ttest_ind_two_sample"]`
- `reported_n: int`
- `n_evidence_kind: Literal["admission_literal", "nearby_total_literal", "ttest_measurement_rows_literal", "two_group_sum"]`
- `group_counts: [] | exactly two {label: str, n: int} objects`
- `admission_template_id: Literal["numbered_measurement_rows", "sampling_day_file_rows", "selected_path_nubbin_rows", "individual_chamber_readings"]`
- `selected_path_binding_kind: Literal["source_file_anchor", "the_file_records_anchor", "direct_admission_path"]`
- `authority_binding_digest: Digest`
- `report_evidence_spans: nonempty array[EvidenceSpan]`

The compiler copies that exact object and its semantic digest into
`x-report-csv-row-entry-evidence` and `x-report-csv-row-entry-evidence-digest` on the reported semantic
assertion and adds a full-file SourceRef for the CSV alongside report-span SourceRefs. The generic
detector remains unchanged. At Finding drafting, the controller passes the already-digest-bound work
packet to the drafter, which requires exactly one reported assertion with this profile and cross-checks
it against the child Answer's authority binding.

The wording profile is
`method-conflict-finding:report-csv-authorized-unit-requirement-conflict-v1`. Its title is fixed:

> Selected report contradicts the frozen one-row-per-authorized-unit requirement

Its summary template is fixed except for JSON-escaped values from the typed projection:

> The frozen method contract requires one analyzed row per value of the human-authorized unit column
> `{COLUMN}` in full-digest `{CSV_PATH}`. For the selected analysis, `{REPORT_PATH}` states that all
> `{N}` CSV rows entered a two-sample `scipy.stats.ttest_ind`-family test as individual observations;
> `{COLUMN}` has `{U}` distinct nonempty values and `{R}` values repeat across those rows. Those two
> frozen representations conflict. This Finding is limited to that contract-versus-report conflict.
> It does not establish that the contract's scientific requirement is correct, that project code
> executed the reported analysis, or that the statistics are invalid. Uninspected project code may
> have pseudobulked or otherwise transformed the table. It also does not establish numerical
> causality, bias direction, universal scientific correctness, or invalidity outside this selected
> analysis.

No report-authored prose, group label, p-value, or arbitrary path is interpolated into the conflict
wording.
Only normalized report/CSV paths, the authorized column, and checked integer facts are slots. The
Finding profile digest covers the exact title, template, slot schema, issue class, severity rationale,
non-inferences, and next action.

## 8. Admission and pin change

Before the blind envelope, the new adapter/check is development-only and can produce at most an
evaluation Finding candidate. The old installed dependence pin must not be pointed at new bytes or old
qualification evidence.

After the sealed envelope passes and Alex accepts the promotion decision:

1. Recompute the unchanged binding ID with check `1.2.0`, evidence plane `reported_text`, the new check
   manifest, and the unchanged generic detector identity.
2. Create a new held-out qualification and metric set bound to the exact adapter implementation,
   manifest, grammar, binding, contract-profile `1.1.0`, and blind protocol bytes.
3. Freeze a threshold policy requiring at least three adjudicated roots, `missed_roots == 0`,
   adjudicated-root recall `1.0`, at least three blind controls, and completed-opportunity false-positive
   rate `0.0`. The global 108/155/new-negative zero-false-Finding gate is an additional absolute release
   gate recorded in the qualification report.
4. Extend `GrantPin` with optional `finding_profile_id` and `finding_profile_digest`. Set both on the
   dependence pin; leave the complete-domain pin's optional fields absent so its authority does not
   change.
5. Replace, in the existing `_DEPENDENCE_PIN` object, the stale binding/check/adapter/qualification/
   metric/threshold fields with the reviewed new values. Do not add a second pin.
6. Require live adapter identity and live Finding-profile identity to match the pin before projection.
7. Rebuild the installed qualification grant resource and dependence part of the production-Finding
   demonstration in the same reviewed change. Until all identities agree, the controller returns the
   evaluation candidate and zero Findings.

The normal route remains:

```text
sc-referee method-contract PROJECT --task TASK --profile PROFILE --actor-id HUMAN --output CONTRACT
sc-referee audit PROJECT --report REPORT --material-input CSV --method-contract-lock CONTRACT/semantic.lock.json --output AUDIT
```

No `demo`, direct adapter call, `dependence_authorization_lock`, new flag, or project-code execution is
allowed in acceptance.

## 9. Batch-K retrospective development check

These four cases are label-visible development checks and do not count toward fresh blind `N`. Each
gets a retrospective `1.1.0` profile using its explicitly documented unit and group/contrast columns
and `data/input.csv`, then runs through the exact normal CLI route above. D1' permits all four CSVs;
the report-wide method join, per-adjacent-pair heading rule, and revised numeric boundary admit three as
evaluation Finding candidates. The unchanged exact selected-path anchor keeps 3ae92 as an honest
development miss. K remains label-visible development evidence and contributes no qualification credit.

| Case | Authority column and exact data fact | Admission/count path | Expected pre-pin / post-pin outcome |
| --- | --- | --- | --- |
| `0de3a6061d3bb4056306` | Unit `plot_id`, group `management`; `N_csv=40`, `U=10`, `R=10`, `M=4`. D1' sole candidate `visit` (`4 <= U`) is a within-unit index; `water_table_cm` (`28`) and `ch4_flux_mg_m2_h` (`40`) are excluded by distinct count. | Form 1 at line 9 binds to the line-5 path anchor. The report-wide Student method at line 9, N/admission, group table, and line-20 result form a 16-line envelope. Its three ATX headings are split so that no adjacent pair contains more than one (`evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/0de3a6061d3bb4056306/results/report.md:5-20`). | One evaluation candidate / zero pre-pin Finding; replay-identical. |
| `6b2da0c7167dbba3738f` | Unit `reactor_id`, group `carbon_source`; `N_csv=60`, `U=10`, `R=10`, `M=6`. D1' sole candidate `run_day` (`6 <= U`) is a within-unit index; the response (`59`) is excluded. | Form 2 binds lines 5 and 17-19. The report-wide Welch method at lines 17-19 and selected result at lines 24-25 form a bounded minimal join; each adjacent-pair interval has at most one heading (`evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/6b2da0c7167dbba3738f/results/report.md:5-25`). | One evaluation candidate / zero pre-pin Finding; replay-identical. |
| `e9e2718573bb47f7d17b` | Unit `colony_id`, group `reef_zone`; `N_csv=48`, `U=12`, `R=12`, `M=4`. D1' candidate `depth_m` (`12 <= U`) is nonindex but its unit pairs repeat; `nubbin_code` (`48`) and response (`44`) are excluded. | Form 3 directly binds the path. The report-wide Welch method at lines 5-8, the per-group `24 + 24` table witness, and the line-18 t/p result form a bounded minimal join (`evaluation/development/dependence-growth-loop/batch-k1/authoring/cases/e9e2718573bb47f7d17b/results/report.md:5-18`). | One evaluation candidate / zero pre-pin Finding; replay-identical. |
| `3ae92d0bb421d6eee99e` | Unit `plot_id`, group `water_table_regime`; `N_csv=60`, `U=12`, `R=12`, `M=5`. D1' sole candidate `survey_round` (`5 <= U`) is a within-unit index; both measurement columns (`60`) are excluded. | The revised numeric boundary accepts sentence-final `p < 0.0001.` and form 4 supplies method/N/result, but the report contains no byte-identical selected CSV path anchor (`evaluation/development/dependence-growth-loop/batch-k2/authoring/cases/3ae92d0bb421d6eee99e/results/report.md:13-18`). | Zero candidate / zero Finding with `selected-csv-path-ambiguous`: retained wrong-file guard and honest development miss. |

The two K binomial cases must also produce zero candidate and zero Finding with reason
`procedure-outside-report-csv-rowwise-ttest-envelope`. The revised development expectation is therefore
3/4 K t-test cases admitted as evaluation candidates, zero production Findings before qualification/pin,
and 0/2 binomial cases admitted. A different result is a development failure;
it is not permission to relax path binding, composite suppression, or the enumerated grammar.

All four pass D1'. The first three pass the report grammar after R1 through R3. Only 3ae92 abstains, and
it does so at the exact selected-path scan before admission binding; its missing path anchor is not
inferred from the CLI-selected input.

## 10. Sealed fresh blind envelope

### 10.1 People and isolation

- Alex supplies or explicitly approves the scientific authority values for all six task/profile pairs
  before any workflow is authored. The recorded `actor_id` must name that actual human; an agent may not
  impersonate scientific authority.
- One independent Claude prompt-author agent, in a fresh isolated session that has never received this
  design, its grammar, K prose, adapter code, or detector output, writes all six blind author prompts.
  Neither Fable nor the builder/Codex writes, edits, selects replacements for, or suggests text for those
  prompts. The agent's six exact prompt byte strings and their ordering are hashed into the envelope
  manifest and frozen before either Fable or the builder reads any prompt.
- After that prompt freeze, Fable is envelope custodian. Fable assigns opaque case IDs, withholds case
  bytes, roles, labels, and detector outputs from the builder, and records every subsequent digest and
  chronology event. Custody does not authorize editing or replacing the frozen prompts.
- Six distinct fresh, mutually isolated author sessions write one project each. Positive authors P1,
  P2, and P3 each receive a different repeated-unit scenario and are asked to commit the row-wise
  `ttest_ind` misstep and report clearly what entered the test, but they are not shown regexes, accepted
  templates, K prose, adapter code, or detector output. Negative authors N1, N2, and N3 respectively
  author (a) a unit-aggregated two-sample analysis, (b) a one-row-per-unit two-sample analysis, and (c) a
  repeated-row analysis explicitly labeled sensitivity-only or using a registered dependence-aware
  safeguard. They likewise receive no grammar bytes.
- One fresh calibrated reviewer, blind to case roles and detector output, produces the scientific label
  before detector execution under ADR-0067's single-review-with-escalation rule. A second reviewer from a
  different model family is used only on ADR-0067's stated escalation conditions. Neither reviewer is a
  builder or author.

The role prompts describe scientific behavior, not exact lexical forms. A positive that does not meet
the frozen predicate is an honest miss and fails the 3/3 bar; it is not rewritten or replaced.

### 10.2 Freeze chronology

1. Accept ADR-0076 and this design.
2. Commission the independent Claude prompt-author agent described in section 10.1. Envelope intake
   freezes the six exact author-prompt byte strings, their fixed case ordering, the prompt-author session
   identity/provenance, and their content digests in the envelope manifest before Fable or the builder is
   permitted to read any prompt. The prompt bundle remains sealed from the builder through step 4.
3. Freeze the implementation closure—contract parser, adapter, grammar, suppressor table, fact profile,
   Finding template, detector/admission code, tests, development expectations, threshold policy, and
   scorer—together with the protocol, reviewer prompt, six task files, six `1.1.0` profiles, human
   approvals, and six exact input CSV byte sets. Record their content digests. No author prompt, case
   output, or label may have been visible to the builder.
4. Using those frozen bytes, run `method-contract` for all six cases before any project author sees or writes
   analysis/report code. Freeze and record each contract lock digest; adding those generated digests to
   the envelope manifest does not reopen any implementation or prompt byte.
5. Release each already-frozen prompt only to its isolated project-author session and invoke each author
   once. Freeze every returned project byte immediately. A failed or incomplete call is
   retained as a failed envelope cell; it is not silently retried or substituted.
6. Run intake/static validation that does not run project-authored code. Freeze the admitted case manifest.
7. Obtain and freeze scientific labels before running the detector.
8. Run the frozen development candidate once on every case and freeze results. If any positive is missed
   or any negative receives a candidate that would be a Finding, the envelope fails; no grammar tuning is
   allowed against it.
9. If and only if the frozen outcomes pass, deterministically derive the qualification, metric set, and
   replacement pin. Alex separately accepts the promotion/install decision.
10. With the accepted pin installed and no adapter, grammar, suppressor, template, or admission changes,
   run the ordinary CLI on the same frozen six projects and their pre-analysis contract locks. Require one
   Finding on P1-P3 and zero Findings on N1-N3.
11. Replay each audit semantic lock model-free and compare the replay projection below.

Any predicate or implementation change after case bytes or labels become visible requires a new adapter
version and a wholly fresh six-case envelope. Installing deterministically derived qualification records
after a passing frozen run is promotion, not detector tuning.

### 10.3 Meaning of replay-identical

“Replay-identical” means byte equality of canonical JSON for the following projection, with arrays sorted
by their stable record IDs:

```json
{
  "detector_results": "complete records",
  "findings": "complete records",
  "coverage_records": "complete records"
}
```

The comparison is between an audit's frozen semantic lock derivation and `sc-referee replay` of that same
lock. Nothing is stripped from those records. SQLite files, storage manifests, HTML rendering, filesystem
mtimes, and a separately initiated audit's fresh run ID/timestamps are not part of this equality. Each
positive must replay the same single Finding ID, wording, evidence refs, fact counts, grant linkage, and
deterministic input digest; each negative must replay the same empty Finding list.

## 11. Test plan

### 11.1 Contract and authority tests

- Accept the complete e9e2718 `1.1.0` record and freeze the exact CSV digest.
- Reject every missing/extra top-level or nested field, path escape, non-CSV path, empty/trimmed column,
  wrong check/candidate, nonhuman actor, unavailable material, and duplicate material identity.
- Prove Answer, assertion, profile-manifest, contract, and semantic-lock digests change on any authority
  mutation.
- Prove parent input or task drift fails closed at audit.
- Replay existing `1.0.0` locks byte-identically and prove they cannot authorize the new lane.
- Prove all other checks accept only `semantic_role_authority: {}` under `1.1.0`.
- Prove the pre-inspection projection and final child binding resolve the same parent Answer and binding
  digest, and that neither duplicate nor mismatched shared derivations are accepted.

### 11.2 CSV tests

- Boundary tests immediately below/at/above the row, column, field-size, and material-byte limits.
- UTF-8, BOM, NUL, newline, quoting, embedded newline, duplicate/blank header, ragged row, blank/trimmed unit,
  missing column, and malformed quote cases.
- Exact multiplicity tests for `N==U`, one repeated unit, all units repeated, case-sensitive unit values,
  and maximum multiplicity.
- For every column position, prove D1' authority/group and distinct-count candidate filtering followed
  by the exact sorted per-unit tuple comparison for candidates, including
  duplicates, empty strings, unequal tuple lengths, and byte ordering. A unique-pair within-unit index must
  not suppress; a unique-pair nonindex must suppress; nonunique pairs must not suppress on this rule; and
  a truncated or incomplete scan must abstain. Include all four K expectations and the closed three-row
  label-collision control from section 4.2.
- Full-digest/path/selection mismatch and more-than-one-material-input tests.

### 11.3 Report grammar tests

- One positive unit test for each accepted test spelling and each of the four admission forms.
- For forms 1, 2, and 4, test both exact selected-path anchor spellings, inline-code path visibility,
  absent/mismatched/duplicate anchors, a second visible CSV path, anchor distance 16/17, and one/two
  intervening headings. Include a byte-exact path-case test in which an uppercase authority path matches
  only identical visible bytes and the case-mismatched report abstains. Form 3 must bind the path directly.
- Test visible-text extraction and whitespace normalization separately for emphasis, strong emphasis,
  inline code/backticks, table cells, link labels, excluded link targets, block boundaries, ASCII and
  non-ASCII whitespace, and every finite-decimal/scientific-notation boundary.
- e9e2718 two-row per-group sum, plus a 3ae92 lexical-form fixture that must abstain without a selected
  path anchor.
- Line-gap tests at 16 and 17; zero/one/two-heading tests for one adjacent-node interval; and a test that
  permits three or more headings across the whole join when each adjacent interval contains at most one.
  Test total envelopes at 40/41 lines; 0de3's path-bound three-heading envelope must pass.
- Prove every accepted spelling is enumerated report-wide as an ordinary method node, the complete join key
  selects the winning occurrence, neutral spellings may coexist, and any report-wide Student/Welch class
  conflict abstains. No marker string or heading name may select the result block.
- Deterministic minimal-join enumeration, coordinate/match tie-break, overlap, and malformed duplicate-node
  tests.
- Equal duplicate totals/results accepted; unequal duplicates rejected.
- Exact negative tests for `independent-samples t-test`, `two independent groups`, bare `N observations`,
  paraphrases, leading-zero/decimal/scientific N, path case mismatch, third group row, unmatched group labels,
  and conflicting Student/Welch declarations.
- One mutation test for every lexical suppressor family, including the new hierarchy, technical-replicate,
  revised-protocol/plan/SAP, randomization-at, and extended-unit-noun forms and negated wording. Test every
  exact/glob token boundary and prove generic `summary`, `summarised`, and `model` alone—and `sum` only as
  a substring—do not trigger a suppressor.
- For `measurements`/`measurement rows` table headers, prove suppressors in table cells, attached captions,
  and the nearest same-section introducing block abstain; prove an unscannable table context abstains.
- Inferential t/p token boundary, comparator, finite-number, separated-list-line, and conflict tests.

### 11.4 Observation, detector, wording, and pin tests

- Prove all four roles, `reported_text`, scope join, report spans, CSV SourceRef, receipt set, and typed fact
  projection are exact.
- Mutate each fact field, digest, SourceRef, child Answer authority, or reported assertion and require no
  Finding.
- Require the unchanged generic detector to produce an exact conflict candidate and all ten finite checks
  to complete.
- Prove the old pin, old qualification, wrong adapter bytes, wrong grammar, wrong contract profile, wrong
  Finding profile, stale binding, qualification threshold failure, and metric mismatch all refuse
  promotion.
- Prove the bounded title/summary is recomputed, not copied from report prose, cannot interpolate
  unverified text, names only the frozen-requirement/report conflict, and preserves the contract-may-be-
  wrong/uninspected-pseudobulk/statistical-invalidity non-inferences exactly.
- Prove complete-domain pin resolution and Findings are unchanged.

### 11.5 End-to-end and corpus gates

- Run the exact normal CLI lifecycle for all four K t-test cases and both K binomial controls; assert the
  revised 3/4 evaluation-candidate and 0/2 binomial expectations and reasons in section 9, zero pre-pin
  production Findings, and model-free replay equality.
- Run all 108 existing blind cases. Score scientific-label positives separately from false accusations;
  require zero Findings on every scientifically negative case and report any true positive as recall, not
  as an FA.
- Run all 155 answer-visible regression cases and require zero false Findings. Cases without valid
  pre-analysis `1.1.0` authority must remain unable to convict; contract-complete near negatives must be
  exercised through the normal route.
- Run all new mutation negatives and the three sealed blind negatives; require zero Findings.
- Require all three sealed blind positives to emit exactly one normal-path Finding and replay identically.
- Re-run the production-Finding demonstration and installed-skill/installed-wheel integrity tests after
  promotion.
- Run the repository-required `ruff check .`, `ruff format --check .`, `mypy src`, `pytest`, and
  `python scripts/validate_starter.py` only during the authorized build, not during this design task
  (`AGENTS.md:46-54`).

## 12. File-by-file implementation estimate

These are inferred change estimates, not edits made in this task. Counts are approximate net logical
lines before generated one-line JSON resources.

| File | Planned change | Rough size |
| --- | --- | ---: |
| `src/sc_referee/scientific_requirement_contract.py` | Version-dispatched `1.0.0` reader plus exact `1.1.0` role authority, snapshot binding, propagation, and verification. | +190 / -35 |
| `src/sc_referee/method_contract_run.py` | Force authority CSV full digest; preflight helper returning verified existing Answer/assertion records; verify current material identity. | +110 / -15 |
| `src/sc_referee/scientific_checks/core.py` | Exact optional `RowEntryEvidenceProjection`; omit when absent to preserve old observation bytes. | +115 / -5 |
| `src/sc_referee/scientific_checks/integration.py` | Freeze verified authority in `shared_derivations`; copy row-entry facts/digest and CSV SourceRef to the reported assertion. | +70 / -10 |
| `src/sc_referee/scientific_checks/report_csv_dependence_adapter.py` | New closed CSV parser, report grammar, joins, suppressors, receipts, facts, and abstentions. | new, about 650 |
| `src/sc_referee/scientific_checks/profiles.py` | Replace active dependence adapter, bump check, retain roles/candidate, register exact counterevidence and known gaps. | +65 / -45 |
| `src/sc_referee/controller.py` | Pre-inspection authority projection; pass exact detector work packet to the Finding drafter; live wording-profile pin check. | +55 / -8 |
| `src/sc_referee/detectors/method_conflict_finding.py` | Dependence fact validator and bounded template/profile digest; leave generic/complete-domain drafting unchanged. | +150 / -15 |
| `src/sc_referee/detectors/method_conflict_grant_pins.py` | Optional Finding-profile pin fields; later replace the existing dependence pin identities only. | +25 plus about 35 replaced lines |
| `src/sc_referee/resources/scientific-check-manifests-v1/registry.json` | Deterministically regenerated check/adapter/binding identities. | generated one line |
| `src/sc_referee/resources/qualification-grants-v1/grant-set.json` | New accepted dependence qualification and replacement grant reference after blind pass. | generated one line |
| `src/sc_referee/resources/qualification-grants-v1/metric-sets.json` | New 3-positive/3-control metrics and absolute gates. | generated one line |
| `docs/implementation/PUBLIC_INTERFACES.md` | Document profile `1.1.0` and existing-flag normal lifecycle. | +35 / -8 |
| `docs/implementation/CAPABILITY_MATURITY_LEDGER.json` | Regenerate exact dependence Finding-qualified basis after promotion. | generated one line |
| `tests/test_method_contract_run.py` | Contract shape, compatibility, tamper, material freeze, and authority-binding tests. | +190 / -20 |
| `tests/test_report_csv_dependence_adapter.py` | Exhaustive CSV/report grammar, suppressor, fact, and boundary matrix. | new, about 850 |
| `tests/test_scientific_check_registry.py` | New check/adapter/binding identities and old-adapter nonactivation. | +65 / -20 |
| `tests/test_scientific_check_integration.py` | Shared authority projection, assertion facts, SourceRefs, and final binding. | +130 / -15 |
| `tests/test_installed_method_conflict_grants.py` | Stale/new pin, wording profile, qualification, complete-domain nonregression. | +150 / -30 |
| `tests/test_general_audit.py` | Ordinary-CLI success/abstention/tamper routes without hidden parameters. | +140 |
| `tests/test_pseudorep_k_development.py` | Four K t-test and two K binomial normal-path development checks. | new, about 240 |
| `tests/test_regression_corpus_runner.py` | False-Finding accounting across all 155 cases. | +70 |
| `tests/test_production_finding_demonstration.py` | Replacement dependence demonstration and exact replay assertions. | +90 / -30 |
| `evaluation/development/pseudorep-k-retrospective-v1/DEVELOPMENT_LEDGER.json` | Paths, authority profiles, expected 3/4 t-test evaluation candidates and 0/2 binomial admissions with the exact retained path reason; qualification-ineligible. | new, about 1 formatted JSON file |
| `evaluation/qualification/authorized-independent-unit-entry-report-csv-v1.2.0/PROTOCOL.json` | Frozen chronology, actors, prompts, digests, thresholds, and no-execution declaration. | new, about 250 |
| `evaluation/qualification/authorized-independent-unit-entry-report-csv-v1.2.0/cases/{P1,P2,P3,N1,N2,N3}/` | Six author-produced projects plus pre-analysis task/profile/contract locks; size unknown until sealed authoring. | six new frozen subtrees |
| `evaluation/qualification/authorized-independent-unit-entry-report-csv-v1.2.0/SCIENTIFIC_LABEL_LEDGER.json` | Label-before-detector review and escalation record. | new, about 150 |
| `evaluation/qualification/authorized-independent-unit-entry-report-csv-v1.2.0/DETECTOR_RUN_LEDGER.json` | Frozen candidate and post-promotion normal-CLI/replay outcomes. | new, about 200 |
| `evaluation/qualification/authorized-independent-unit-entry-report-csv-v1.2.0/QUALIFICATION_REPORT.md` | 3/3, 0/3, global 0-FA accounting, limitations, and promotion recommendation/no-recommendation. | new, about 180 |
| `evaluation/qualification/authorized-independent-unit-entry-report-csv-v1.2.0/MANIFEST.sha256` | Content-digest closure for the envelope. | new, generated |
| `evaluation/production-finding-demonstration-v1/dependence/` | Replace the old hidden-lock demonstration with report/CSV contract-bound error/control and replays; retain prior demonstration as history if moved under a versioned sibling. | regenerated subtree |
| `evaluation/production-finding-demonstration-v1/DEMONSTRATION_RECORD.json` and `MANIFEST.sha256` | Recompute top-level identities and assertions. | two generated files |

No file in `src/sc_referee/dependence_recognition_v2/`, Slice C, execution/security, pure reader-form,
or run-40 is changed by this slice.

## 13. Observed, inferred, and verification-needed claims

### Observed

- The CLI, context, role, detector, and pin surfaces cited in sections 1 and 2 exist today.
- The four K reports contain the four row-entry phrasings and count arrangements stated in section 9;
  only three can bind a selected path under the revised forms
  (`docs/implementation/RECALL-RECON-2026-08-21.md:366-442`).
- Under D1', the complete distinct counts and candidate outcomes for every K t-test CSV are those
  enumerated in sections 4.2 and 9. None triggers the composite suppressor; the four development
  outcomes are three evaluation candidates and one selected-path abstention.
- Current public Answer schema can carry the proposed structured value and `x-` extensions without a
  public schema version change.
- The current hidden dependence authority parameters are not exposed by the normal CLI
  (`src/sc_referee/controller.py:667-696`; `src/sc_referee/cli.py:682-734`).

### Inferred design choices

- At design time, profile `1.1.0`, the exact field names, count bounds, lexical templates, 16-line join,
  suppressor vocabulary, active-adapter replacement, Finding template, and file estimates were proposed.
  The implemented outcomes and deliberately narrower readings are recorded in BUILD-NOTES below.
- R2 removes the complete-envelope heading-count cap while retaining the per-adjacent-pair cap; 0de3's
  three-heading join is now exercised as an accepted evaluation candidate. D1' independently permits all
  four K t-test CSVs.
- The generic detector remains byte-identical. Domain facts travel in its existing work packet and are
  validated only by the downstream drafter.

### Claims requiring build-time verification

- Verified in this build: all four K profiles bind their full CSV digest; three reach evaluation-candidate
  state and 3ae92 reaches the exact selected-path abstention through the normal route; both binomial
  controls abstain; all six replays are identical.
- Verified in this build: the adapter-local omitted-when-absent row-entry fact preserves the core
  observation type and unrelated adapters; the generated release registry pins the new adapter bytes.
- Verified in this build: the complete-domain pin, qualification, and committed demonstration continue
  to replay; the stale historical dependence pin is ineligible and publishes no capability.
- Verified in this build: v0.19.0 validates the extended Answer/assertion route without schema edits.
- Verified in this build: 107 materialized blind workspaces plus the one retained intake refusal account
  for all 108 lifetime cases; the 107 audits emit zero Findings and replay identically. The 155-case
  answer-visible runner passes with zero Findings, zero project execution, zero model calls, and exact
  replay for all four materialized direct-audit cases.

## Open questions that would change the build

None for the authorized implementation. Acceptance of the derived promotion record remains a separate
gate, and the actual human `actor_id` values for the later blind contracts must be supplied honestly
before authoring; neither is part of this build.

## BUILD-NOTES

- **D1 superseded by D1'.** Candidate selection excludes the authority-named unit and group/contrast
  columns and every column whose complete-domain distinct count exceeds `U`; no type, response, or
  identifier semantics are inferred. Only then is the exact within-unit-index/unique-pair rule applied.
  The K and label-collision outcomes are frozen in sections 4.2 and 9.
- **R1 reverses D3 without adding a semantic join.** The `outside` veto is deleted. Every report-wide
  accepted spelling is an ordinary rank-0 method-node candidate, and the existing complete minimal-join
  key chooses the occurrence under the unchanged adjacency and envelope limits. Exactly one normalized
  result node remains mandatory. As a tighter report-wide guard, all non-neutral spellings must normalize
  to at most one Student/Welch class; a class conflict abstains even if one occurrence could join locally.
- **R2 removes only the whole-envelope heading count.** Every adjacent ordered-node interval still permits
  at most one ATX heading and the total envelope remains capped at 40 physical lines. There is no total
  heading-count cap. Consequently 0de3's three headings pass because they occupy separate adjacent-pair
  domains (one is inside its compound admission); no interval rule was loosened for that case.
- **R3 distinguishes punctuation from another decimal component.** The exact numeric right boundary is
  `(?![A-Za-z0-9_])(?!\.[0-9])`. It admits a sentence-final period after a p-value while refusing to lex
  `0.0001` out of `0.0001.5`. Therefore 3ae92 reaches, and still fails, the independently mandatory
  selected-path anchor check.
- **F1 path matching is byte-identical.** Visible blocks retain both whitespace-normalized original-case
  text and a separate ASCII-folded lexical view. CSV discovery and selected-path binding consume the
  original-case view; all phrase grammar remains on the folded view. An uppercase authority path matches
  only identical visible bytes. The visible-path right boundary admits sentence punctuation but rejects a
  longer `.csv` suffix; this is a fail-closed second-path scan, not positive evidence widening.
- **F2 random-effect glob is plural-safe.** The suppressor is the exact consecutive-token glob
  `random effect*`, so both `random effect` and `random effects` abstain. No other `random*` prose is added.
- **F3 closes the missing mechanical boundaries.** Tests now cover absent, mismatched, duplicate,
  case-mismatched, 16/17-line, and second-visible-CSV anchors, plus the exact row, column, and field-size
  CSV limits. These tests do not create a new admission family or a new accepted data shape.
- **Adapter-local fact projection.** The row-entry fact is an omitted-when-absent subclass projection in
  the new adapter rather than a field added to `scientific_checks/core.py`. This preserves every existing
  core and unrelated adapter implementation digest while integration consumes the projection only by
  exact attribute presence; it narrows the planned change surface without widening conviction.
- **Report-wide N conflict is narrower than conviction.** If any closed N-witness form anywhere in the
  selected report disagrees with `N_csv`, the implementation abstains even when that witness might fall
  outside a surviving target join. The design's joined-target wording could be read more narrowly; this
  implementation chooses the miss-producing reading and does not discard contradictory report evidence.
- **Unsupported inline composition fails closed.** Raw inline HTML and malformed residual link syntax
  abstain instead of attempting partial visible-text recovery. Valid link labels remain visible while
  destinations remain unavailable as evidence, exactly as section 4.3 requires.
- **Retained stale pin handling.** The existing dependence pin remains retained but cannot match check
  `1.2.0`. Capability projection and the private maturity ledger skip that stale retained entry instead
  of treating it as a current installed capability; the complete-domain pin is unchanged and remains
  live. This required small `capability_matrix.py` and `capability_maturity_ledger.py` integration edits
  omitted from the original rough file estimate.
- **Regression metadata refresh only.** Activating check `1.2.0` and changing the two existing test-module
  helpers changed the regression ledger's component/test-source identities. The 155 case rows, selectors,
  labels, retained trees, and qualification exclusions are unchanged; only those identities, the expected
  no-authority disclosure classification (`not applicable` to `unsupported`), and enclosing canonical
  ledger/plan digests were refreshed.
- **Shared integration dependency identity.** Adding the optional exact row-entry projection to shared
  integration changes the founder semantic adapter's dependency-closure manifest/implementation identity.
  Its check manifest, behavior, and core observation bytes remain unchanged; the release-registry tests
  pin the new closure identity.
- **No promotion artifacts.** This build creates no blind prompt, qualification envelope, metric set,
  grant, replacement dependence pin, capability-maturity entry, or production demonstration. A synthetic
  admitted observation therefore remains an evaluation Finding candidate and emits zero production
  Findings until the independent sealed envelope passes and Alex separately authorizes promotion.
