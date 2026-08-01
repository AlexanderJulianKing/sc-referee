# Migration from v0.15.0 to v0.16.0

The migration is fail closed. It versions ordinary records and adds the new empty static public
input collections where applicable. Existing v0.15 static profiles, proofs, fixtures, dependent
case outcomes, and metric evidence are retained only as namespaced legacy payloads because a bare
public bundle cannot replay the new discriminated proof and private source-validation closure. It
creates no second profile, Answer, proof, qualification, maturity, Finding, or execution authority.
