# Data Description: Groundwater Quality Monitoring Network

## Overview
A quarterly groundwater quality dataset from four monitoring wells in a mixed hydrogeological setting. Monthly samples collected January–March 2025 characterize water chemistry across shallow aquifer zones.

## Sampling Network
- **Wells W-01, W-03**: Background/reference wells in uncontaminated zones
- **Well W-02**: Higher mineralization zone (natural conductivity signature)
- **Well W-04**: Agricultural area with potential nutrient loading
- **Frequency**: Monthly (3 events, 12 total records)
- **Measured depth**: Shallow groundwater (5–15 m below surface)

## Measured Variables
- **pH**: Acidity/alkalinity (scale 0–14). Values 6.8–7.9 indicate neutral to slightly alkaline water typical of carbonate aquifers
- **conductivity_uS**: Electrical conductivity in microsiemens per cm; proportional to dissolved ions and salinity
- **dissolved_oxygen_mg_L**: Oxygen concentration in mg/L; essential indicator of aerobic vs. anaerobic conditions
- **temperature_C**: Water temperature in °C; reflects seasonal variation and depth
- **nitrate_mg_L**: Nitrogen as NO₃⁻ in mg/L; primary indicator of fertilizer or waste contamination (EPA drinking water standard: 10 mg/L)

## Sampling Methods
- Field measurements: pH, conductivity, temperature (calibrated probes)
- Laboratory analysis: dissolved oxygen (Winkler titration), nitrate (ion chromatography)
- Quality assurance: replicate analysis, external standards, and IQR-based outlier screening
