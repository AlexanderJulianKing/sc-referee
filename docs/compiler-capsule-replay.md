# Compiler capsule replay determinism

`sc_referee.compiler.capsule` freezes the resolved `BindingProposal`, all four ceremony answers,
raw source-member byte digests, the registered derivation implementation digest, estimator and
compiled-authority identities, and the resulting finding identities. Replay verifies those frozen
members and then calls only `compile_from_proposal(capsule.proposal, folder, capsule.answers)`.
During that call, every repository model-client resolver is replaced with a hard-error guard. A
model client is neither resolved nor constructed; an attempted resolution fails the replay.

The capsule records Python, NumPy, pandas, SciPy, OS/platform, machine, and byte-order identity.
Byte-identical finding and evidence identities are guaranteed only when this environment identity
matches. Estimator digests use `canonical-float-digest-v1`, which rounds derived finite values to
12 significant decimal digits before hashing (approximately a 5e-12 relative rounding budget
away from zero, with signed zero normalized). This reduces ordinary last-bit drift from division,
means, and numeric libraries, but does not eliminate cross-machine divergence: values on a
quantization boundary can still round differently, and LAPACK/BLAS algorithms can differ by more
than the budget. A different environment does not hard-fail: replay still runs and returns the
typed `ENVIRONMENT_MISMATCH` result, explicitly withholding the byte-identical guarantee even if
the captured identities happen to match. Cross-machine byte identity is not claimed.

Folder/proposal compilation hashes the raw bytes of each bound source file. Archive compilation
hashes the raw compressed member bytes. The in-memory table API, which has no source bytes, uses
`gbp07-source-digest-v2`: ordered columns and normalized semantic dtype tags are encoded with typed
null, boolean, integer, float, string, and byte scalars; row order is binding, the incidental pandas
index is excluded, and float signed zero is normalized to positive zero. Every source-digest map
records its `digest_policy_version`.

Changed source bytes, proposal or answer members, derivation registry implementation, target
coefficient, or genotype assignment never silently refresh the capsule. They produce a typed
invalidation or mismatch and require a newly reviewed capsule.
