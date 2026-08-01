# Migration from v0.14.0 to v0.15.0

The migration is fail closed. It versions existing records, adds empty static profile/proof bundle
collections, annotates case outcomes with their pre-existing proof family, and removes authoritative
metric sets whose new family strata cannot be reconstructed from a bare public bundle. It creates
no static fixture, proof, qualification metric, maturity, Finding permission, or execution authority.
