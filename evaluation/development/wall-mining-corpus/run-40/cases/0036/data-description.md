## Recycled Material Contamination Data

**Source**: Industrial materials processing facility operating five material recovery streams.

**Collection Method**: Automated optical scanning system measures foreign material contamination in 1kg representative samples from each completed batch.

**Time Period**: January 5 - February 13, 2026 (40 consecutive batches)

**Variables**:
- **batch_id**: Unique batch identifier (B001-B040)
- **material_type**: Stream classification - Plastic (film/rigid), Metal (aluminum/steel/tin), Paper (cardboard/mixed fiber), Glass (container), Composite (multi-material)
- **contamination_percent**: Percentage of non-target material detected via optical analysis (0-5% range)
- **batch_date**: Processing date in YYYY-MM-DD format
- **batch_size_kg**: Total batch weight processed (350-780 kg range)

**Quality Standard**: Facility quality threshold is 3.0% contamination. Batches exceeding this limit require manual sorting remediation before sale or further processing.

**Context**: Each material stream has distinct source streams and contamination profiles. Composite materials typically show highest contamination due to mixed source materials. Glass and Metal streams show lowest contamination rates due to density-based pre-sorting.