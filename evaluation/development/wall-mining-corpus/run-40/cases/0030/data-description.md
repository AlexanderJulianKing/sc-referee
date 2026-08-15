## Concrete Mixture Composition and Compressive Strength Data

This dataset contains results from 20 laboratory concrete mixture trials investigating relationships between material composition, curing duration, and resulting compressive strength.

**Variables:**
- **sample_id**: Unique mixture identifier
- **cement_kg_m3**: Portland cement content per cubic meter
- **water_kg_m3**: Potable water content per cubic meter
- **fine_aggregate_kg_m3**: Sand/fine aggregate content per cubic meter
- **coarse_aggregate_kg_m3**: Gravel/coarse aggregate content per cubic meter
- **superplasticizer_kg_m3**: High-range water reducer admixture dosage
- **curing_days**: Age of specimen at compression testing
- **compressive_strength_mpa**: Measured compressive strength in megapascals

**Collection Context:** Cylindrical concrete specimens (150×300 mm) cast from systematically varied mixture designs. Testing performed per ASTM C39 standards using hydraulic compression machine. Samples cured in moist conditions at 23°C before testing.

**Design Rationale:** Cement content varied from 250–450 kg/m³ (typical range for structural concrete). Water-cement ratios range 0.38–0.88, creating expected strength variation from 15–42 MPa. Curing ages (7, 14, 28, 56 days) capture strength development timeline. Superplasticizer (0–10 kg/m³) addresses workability at lower w/c ratios.

**Expected Relationships:** Strength increases with cement content, decreases with water content, and increases with curing time.
