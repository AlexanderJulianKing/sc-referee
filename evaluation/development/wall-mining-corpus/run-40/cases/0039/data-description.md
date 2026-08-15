# Building Energy Efficiency Dataset

## Overview
Annual energy consumption data for 35 commercial and institutional buildings, including structural characteristics and system ages that affect operational costs. Data compiled from utility billing records, building permits, and facility maintenance records over a single calendar year.

## Variables

- **building_id**: Unique identifier (B001-B035)
- **age_years**: Years since original construction (range: 6-50 years)
- **square_feet**: Total conditioned floor area (range: 6,600-19,600 sq ft)
- **hvac_age_years**: Age of heating/cooling system equipment (range: 1-23 years)
- **insulation_rating**: Building envelope insulation quality rating on 1-5 scale, where 1=poor/older construction and 5=excellent/modern standards
- **num_floors**: Number of building stories (range: 2-5)
- **annual_energy_cost**: Total annual energy expenditure including electricity and heating in USD (range: $4,200-$13,300)

## Data Characteristics
Buildings represent mixed commercial and institutional use (office, school, and healthcare facilities) across urban and suburban locations. Energy costs reflect typical utility rates for the region. HVAC systems are generally 1-8 years younger than buildings, reflecting periodic replacement cycles.