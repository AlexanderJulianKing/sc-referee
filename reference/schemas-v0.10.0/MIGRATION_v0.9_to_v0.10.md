# Migration from v0.9.0 to v0.10.0

Add empty Stage-3 evaluation collections and classify every legacy BenchmarkFixture as public
development evidence. Keep frozen BenchmarkAdjudication Stage-3 back-references empty. Do not infer
an evaluation candidate, candidate/root mapping, case outcome, metric, interval, or promotion.
Legacy open-ended quantitative metric objects are preserved only in namespaced migration metadata.
A legacy promoted DetectorQualification becomes deferred with experimental effective maturity until
typed metric evidence and a later accepted numeric-threshold policy exist. Do not carry forward a
StorageManifest because migrated bytes require a new manifest.
