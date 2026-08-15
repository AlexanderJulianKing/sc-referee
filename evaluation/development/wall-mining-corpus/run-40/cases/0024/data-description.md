# Concrete Compressive Strength Testing Dataset

## Overview
Laboratory measurements of concrete compressive strength under controlled curing conditions. This dataset captures the mechanical properties of concrete test specimens as a function of curing time and environmental factors.

## Variables

**Curing_Days** (integer, days)
- Number of days the concrete sample cured before destructive testing
- Values: 7, 14, 28, 56 days
- Represents standard testing ages in concrete quality control

**Temperature_C** (float, degrees Celsius)
- Ambient air temperature during the curing phase
- Range: 19.8 to 22.1°C
- Represents laboratory temperature control during hydration

**Humidity_Percent** (float, percent)
- Relative humidity of the curing environment
- Range: 62 to 67%
- Controls moisture availability during cement hydration

**Strength_MPa** (float, megapascals)
- Compressive strength measured by uniaxial compression testing
- Range: 17.2 to 52.1 MPa
- Outcome variable; higher values indicate stronger concrete

## Data Collection

- **Total Records**: 30 test specimens
- **Replication**: 5 samples per curing age at each condition
- **Testing Standard**: ASTM C39/C39M (Compressive Strength of Cylindrical Concrete Specimens)
- **Specimen Geometry**: Standard 10 cm diameter × 20 cm height cylinders
- **Test Method**: Monotonic compression until failure

## Characteristics

Concrete strength increases with curing time due to ongoing hydration reactions of Portland cement minerals. Temperature accelerates hydration kinetics, while humidity influences capillary water availability. This dataset demonstrates typical laboratory variability in strength measurements and the dominant effect of curing duration on concrete development.
