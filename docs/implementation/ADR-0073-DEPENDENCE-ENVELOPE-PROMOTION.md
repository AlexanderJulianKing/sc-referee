# ADR-0073: Promote the exam-time dependence envelope

- **Status:** Accepted by the maintainer on 2026-08-10, in session ("go ahead with the qualification report and promotion")
- **Date:** 2026-08-10
- **Scope:** `check:authorized-independent-unit-entry-into-row-independent-procedure` version
  `1.1.0` under
  `method-conflict-binding:authorized-independent-unit-entry-into-row-independent-procedure-v1`,
  at the exact exam-time bytes below. This decision does not promote the generic detector or any
  sibling binding.
- **Relates to:** ADR-0062, ADR-0066, ADR-0067, ADR-0068, ADR-0069, ADR-0071, ADR-0072, and
  Experiment 0058
- **Finding impact:** None in Round 1. The production grant registry remains empty and the
  controller remains disconnected from private qualification records.
- **Execution impact:** None

## Context

ADR-0072 accepted, before the threshold rehearsal, a one-shot two-of-two sensitivity bar and a
zero-of-five control false-accusation bar. The threshold rehearsal subsequently passed 7/7 but did
not inform those bars. The sealed examination then completed all seven heldout cells on its first
and only attempt: two demonstrated errors produced bounded evaluation candidates, and all five
controls produced no candidate. The retained report records deterministic replay, zero production
Findings, and no project-authored-code execution by the static audit. Intake sandbox execution was
fixture ground truth, not recognizer evidence.

The development history includes two refused pilots as well as two completed pilots. Pilot a
stopped review-unresolved after both official blind reviewers unanimously rejected the answer key;
pilot b stopped at intake because the byte-frozen template had not been stated byte-exactly to its
authors. Neither detector ran. Pilots c and d then passed 6/6 each with zero false accusations.
This decision retains those outcomes rather than treating protocol refusal as detector evidence.

Unlike ADR-0071, the exam-time dependence tuple is byte-identical to the live checkout at this
decision. The heldout authoring protocol binds the live registry content digest and the exact
dependence check, adapter, grammar, binding, and detector tuple. The retained exam audit's detector
manifest is also byte-identical to the current detector manifest. No drift substitution or frozen-
binding reconstruction is needed for the Round-1 resolver proof.

## Decision

1. **Promote the exact examined binding.** The maintainer promotes
   `check:authorized-independent-unit-entry-into-row-independent-procedure` version `1.1.0` under
   binding
   `method-conflict-binding:authorized-independent-unit-entry-into-row-independent-procedure-v1`
   to requested and effective maturity `validated`. Evidence is the sealed ADR-0072 exam: 7/7
   complete cases, two of two bounded true-positive candidates, and zero candidates on five
   controls. This is binding-level maturity only.

2. **Pin the exam-time identities.** Authority is limited to this exact set, copied from
   `heldout-seven-case/authoring/AUTHORING_PROTOCOL.json`, its bound scientific-check registry, and
   the retained exam detector manifest:

   - adapter ID/version:
     `adapter:authorized-independent-unit-entry-into-row-independent-procedure:dependence-semantic-v1`
     / `1.1.0`;
   - adapter implementation digest:
     `sha256:d5d22803d309ddda51651bcc033cb3e5aa4e093988550fb489b7e9671e289c54`;
   - adapter manifest digest:
     `sha256:81df54974a949648f6f86287df725c1a69ce63f41100480d299680f92eee3776`;
   - recognition grammar digest:
     `sha256:bb3b283145ec1420491771ca49fbd2214e553602a735af2a6f7027980c8be873`;
   - detector tuple digest:
     `sha256:252ef70a22da2e2168b26d7477bb0e666f6188d3786f0c41f2034356ab630795`;
   - production binding digest:
     `sha256:e212bf6f81ec30490c817cb810ce5214a160a5841b564019b10b8061ddc0cb16`;
   - detector manifest digest:
     `sha256:5b74ec663a651bd3e2eb934c25896cfbbe02f6840e2ea898296c0d478aa97e0a`;
   - check manifest digest:
     `sha256:4f48a3104693cd6cdcf215bd620b59449ee87c3cd969ddbe7285f168e598ab21`;
   - exam-time scientific-check registry content digest:
     `sha256:086db3b7dd0ebbb9e430763efcc6c1e981e22ea3db2b7e6b8200a51d3d38c253`.

   Every pin above matches HEAD at this decision. This exact pin-vs-HEAD equality is the material
   difference from ADR-0071, whose examined adapter identity had drifted before promotion.

3. **Translate only the pre-label bars.** The digest-verified exam opening records
   `two_of_two_positives` and `zero_of_five_controls`. The private numeric policy therefore requires
   `adjudicated_root_recall`, statistic `estimate`, operator `at_least`, threshold `1.0`, with at
   least two adjudicated roots; and `completed_opportunity_false_positive_rate`, statistic
   `estimate`, operator `at_most`, threshold `0.0`, with at least five control cases. Minimum counts
   are seven workflows, seven problem clusters, two roots, and five controls. The achieved values
   equal the frozen bars; there is no ADR-0071-style policy/achievement mismatch.

4. **Require the absolute root gate now.** The same private policy carries one closed absolute
   count requirement: `missed_roots` must equal zero. The evaluation-private projector and record
   builder admit and enforce only that exact count form. This makes the strict two-of-two decision
   explicit rather than relying only on a ratio or floor. The shared resolver is unchanged; Round 2
   must pin and enforce the absolute gate at installation. This decision does not install a grant
   or wire a production controller.

5. **Reconcile the qualification gates explicitly.** For this binding:

   - pre-case identity, opaque assignments, and threshold authority are satisfied by the lane
     freeze, sealed briefs, ADR-0072, heldout opening, and authoring protocol;
   - fresh error, independently renamed error, corrected, valid-alternative, hard-negative,
     ambiguous, and unsupported cells are satisfied by the seven frozen roles and label ledger;
   - blind review uses ADR-0067's one calibrated agent review with conditional escalation, under
     ADR-0066's accepted single-provider composition; the heldout review was clean and did not
     escalate;
   - seven static detector audits are digest-locked and replayed. A separate Stage-3 comparison
     artifact does not exist; the maintainer accepts the disclosed ADR-0068 lean-consolidated
     audit/review evidence for this binding, as in ADR-0071;
   - pilot-informed bars were accepted before the rehearsal and before heldout labels;
   - recomputed clustered metrics satisfy every minimum, ratio, and absolute count gate;
   - no false accusation or unresolved heldout disagreement existed. The corresponding regression-
     fixture and disagreement-exclusion safety gates are therefore vacuously true for this exam;
     and
   - the qualification report and this explicit maintainer decision satisfy the public-report and
     promotion-decision gates.

6. **Record private proof without installing authority.** Round 1 retains one evaluation-private
   DetectorQualification and QualificationMetricSet under the lane's additive `promotion/`
   directory. The existing fail-closed generic resolver returns one `validated` grant for the exact
   live dependence binding and refuses every sibling or simulated identity drift.
   The resolved private identities are qualification
   `qualification:authorized-independent-unit-entry-v110-round1` with semantic digest
   `sha256:892903989a440c73201057ee810531eb7c38b40684967e1d35b0db6935818f77`, metric set
   `qualification-metric-set:2cb4edfc83dd3eea382e` with semantic digest
   `sha256:735e2d3f87f2825235ac0ca9e0c0b5322176c7fc0e09803f6b33165bdca98104`, and threshold-policy
   digest `sha256:5472a0cb22db56b052c9b6f37ad5e62d71f129524e3880045c033bab998ffdb1`.
   `qualification-manifests.json` remains byte-identical and empty, the detector manifest remains
   `experimental`, every production binding retains `production_finding_permitted: false`, and no
   controller consumes these records. The resolver vocabulary still records `review_basis:
   agent_panel`; the report and ADR-0067 disclose that the actual basis was one calibrated blind
   agent review with escalation available. Experiment 0058 is an input to the registered adapter's
   semantic closure, so its bytes and embedded Stage-5 status remain frozen; this ADR, the public
   report, maturity note, roadmap, and delivery log carry the later binding-promotion status without
   changing the examined adapter identity.

7. **Record score movement per track.** Track 1 remains **1/10 promoted**, unchanged: its
   complete-domain envelope was already the sole promoted member of the ten-error-class delivery
   matrix. Track 2 now has its **first capability family qualified and promoted**: the narrow
   dependence/pseudoreplication binding in this ADR. Track 2 is a separate six-family roadmap and
   does not increment or rewrite Track 1's 1/10 score. Neither track gains a product-wired member.

8. **Keep Round 2 out of scope.** Production wiring is a separate authority change shared with
   the complete-domain envelope's Round 2. It requires an accepted forward public schema,
   installation of content-addressed grants with externally pinned threshold-policy digests,
   production-controller wiring, and exact live-byte revalidation at installation. This Round-1
   resolver proof, private promotion record, roadmap status, or delivery-log entry cannot substitute
   for any of those gates.

## Consequences

- The dependence family is honestly recorded as qualified and maintainer-promoted at one exact
  binding and tuple, while its installed-product and production-Finding state remains unchanged.
- The evaluation-private projector verifies all six published opening/ledger digests, the complete
  seven-case role/outcome set, the exact exam tuple, and the ADR-0072 bars before compiling metrics.
- The report retains all ADR-0072 rule-5 asymmetries: role-derived authority, reviewer/requirements
  evidence asymmetry, `k1`-only covered-negative scope, the review sentence's one-directional paired-
  procedure effect, and unblinded post-intake authority-lock minting. It also discloses agent-only
  review, single-provider composition, and acceptance-before-rehearsal ordering.
- Qualification does not generalize to paired-procedure operand validation, aggregation, pandas,
  other unit-key namespaces, unpinned runtimes, other workflow shapes, or sibling scientific-check
  bindings.
- Zero observed false accusations and two observed positives are narrow evidence, not a correctness
  certificate or domain-wide pseudoreplication authority.

## 2026-08-11 amendment: active-schema identity movement

Section 2's statement that every exam-time pin matched HEAD is factual at this ADR's acceptance
commit. Acceptance of schema v0.19.0 subsequently changed the schema-version-bearing production
binding digest from
`sha256:e212bf6f81ec30490c817cb810ce5214a160a5841b564019b10b8061ddc0cb16`
to `sha256:4a62385441043681dca65005be3c73a11858449955104dc8efe0582606331787`
and the detector-manifest digest from
`sha256:5b74ec663a651bd3e2eb934c25896cfbbe02f6840e2ea898296c0d478aa97e0a`
to `sha256:05738abe8845442b25b9d03d35b5a5696f169ca46057aabd970561dd5bbf909e`.
It did not change this ADR's adapter implementation, adapter manifest, recognition-grammar, or
check-manifest pins:
`sha256:d5d22803d309ddda51651bcc033cb3e5aa4e093988550fb489b7e9671e289c54`,
`sha256:81df54974a949648f6f86287df725c1a69ce63f41100480d299680f92eee3776`,
`sha256:bb3b283145ec1420491771ca49fbd2214e553602a735af2a6f7027980c8be873`,
and `sha256:4f48a3104693cd6cdcf215bd620b59449ee87c3cd969ddbe7285f168e598ab21`.

ADR-0074's separate complete-domain ruling identities are likewise unaffected: recognition
grammar `sha256:c757692071a6925a5ca5e409dc0ad79f7421fcdbc93fb15c14efb30050524362`,
HEAD adapter implementation
`sha256:cb6de94e39efdf726cc516178b77b85443044415b72c8671025ef9c2e6eef05c`,
HEAD adapter manifest
`sha256:231046e541e1e84671b7fe716a2454c67d2d931f1cfe432e7de80512987d3a20`,
and replay semantic digest
`sha256:2c8fc8cbbb22912768cde8b43b00aff22b8de5a0d999b31972d3c3e3b44b87ca`.

The Round-2 `promotion-round2/` records carry the active v0.19 pins. This movement was predicted
by the Round-2 plan's F2 and remains fail-closed in
`test_exam_time_detector_tuple_is_retained_while_live_binding_identity_drifts_at_v019`,
`test_round1_private_records_rederive_but_require_v019_restamp`, and
`test_sibling_bindings_and_simulated_current_drift_defeat_grant`; the current-pin acceptance path
is separately pinned by
`test_round2_records_rederive_at_current_pins_and_resolve_test_local_grant`.
