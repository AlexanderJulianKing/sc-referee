# Dataset: Winter Wheat Yield and Soil Conditions

## Overview
This dataset contains measurements from 15 winter wheat production plots, recording soil chemical properties, growing season weather variables, and resulting grain yields. Data was collected across a single 160-day growing season in a temperate continental climate region.

## Variables
- **plot_id**: Plot identifier (1–15), unique integer designation
- **soil_ph**: Soil acidity/alkalinity measured on pH scale; range 5.9–7.2 (acidic to neutral)
- **soil_nitrogen_mg_kg**: Plant-available nitrogen determined by Kjeldahl digestion; range 37.9–60.2 mg/kg
- **soil_potassium_mg_kg**: Exchangeable potassium extracted with ammonium acetate; range 162.1–215.7 mg/kg
- **rainfall_mm**: Cumulative precipitation during growing season; range 575–740 mm
- **temperature_mean_c**: Mean daily temperature over growing period; range 17.4–20.5°C
- **growing_season_days**: Number of days from planting to harvest maturity; range 151–162 days
- **yield_kg_per_hectare**: Harvested grain yield dried to 14% moisture content; range 4,380–5,520 kg/ha

## Data Collection Methods
Soil samples (0–20 cm depth) were collected at planting from three locations per plot, composited, and analyzed using standard agronomic procedures. Weather data were recorded from automated stations located within 5 km of each plot. Final yields were determined from harvesting entire plot areas and adjusting to standard moisture content.

## Data Quality
No missing values. All measurements conducted using certified analytical methods and equipment. Soil nutrient values reflect natural field-scale variability; no obvious transcription errors or statistical outliers detected.