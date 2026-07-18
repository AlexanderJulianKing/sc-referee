"""Hard-mapped citation registry, keyed by check id.

Hard-mapped (never LLM-generated) so a check can never hallucinate its provenance.
Strings verified against the literature before shipping.
"""
from __future__ import annotations

CITATIONS = {
    "experimental_unit": [
        "Squair et al. 2021, Nat Commun 12:5692",
        "Zimmerman et al. 2021, Nat Commun 12:738",
    ],
    "confounding": ["Leek et al. 2010, Nat Rev Genet 11:733"],
    "confounding_strong": ["Leek et al. 2010, Nat Rev Genet 11:733"],
    "confounding_random_intercept": ["Leek et al. 2010, Nat Rev Genet 11:733"],
    "confounding_random_intercept_conditional": ["Leek et al. 2010, Nat Rev Genet 11:733"],
    "contamination_confound": ["Leek et al. 2010, Nat Rev Genet 11:733"],
    "multiple_testing": ["Benjamini & Hochberg 1995, J R Stat Soc B 57:289"],
    "count_model": [
        "Love et al. 2014, Genome Biol 15:550",
        "Robinson et al. 2010, Bioinformatics 26:139",
    ],
    # Kriegeskorte coined "double dipping" (circular analysis) — the canonical, verified reference.
    # The count-splitting citation (Neufeld et al.) is deferred until the recompute verifier is built
    # and its exact volume:page is verified against the primary source (no fabricated citations).
    "double_dipping": ["Kriegeskorte et al. 2009, Nat Neurosci 12:535"],
    "effect_size_threshold": ["McCarthy & Smyth 2009, Bioinformatics 25:765"],  # TREAT: test vs a fold-change threshold
    # pseudobulk construction integrity — the same pseudoreplication/pseudobulk literature as
    # experimental_unit (aggregate to the replicate, feed a count model raw counts).
    "pseudobulk_integrity": [
        "Squair et al. 2021, Nat Commun 12:5692",
        "Zimmerman et al. 2021, Nat Commun 12:738",
    ],
    # pairing / within-subject structure — the same mixed-model literature (donors as a random/paired
    # effect); ignoring within-subject pairing is the inefficiency these papers quantify.
    "pairing": [
        "Zimmerman et al. 2021, Nat Commun 12:738",
        "Squair et al. 2021, Nat Commun 12:5692",
    ],
    "allele_orientation": [
        "Winkler et al. 2014, Nat Protoc 9:1192",
        "Shabalin 2012, Bioinformatics 28:1353",
    ],
    "eqtl_design_support": ["Shabalin 2012, Bioinformatics 28:1353"],
    "hic_loop_strength": [
        "Venev et al. 2024, PLoS Comput Biol 20:e1012067",
        "Imakaev et al. 2012, Nat Methods 9:999",
    ],
}
