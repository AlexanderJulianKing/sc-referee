## Air Quality Monitoring Dataset

This dataset contains daily air quality measurements from paired urban and rural monitoring stations. Each record represents a single day's measurement from one monitoring location, captured with an automated PM2.5 analyzer equipped with a built-in quality validation algorithm.

The study compares fine particulate matter (PM2.5) concentrations—particles with diameter 2.5 micrometers or smaller—between urban and rural sites. Urban sites are characterized by proximity to vehicle traffic, commercial activity, and building heating; rural sites are located in agricultural areas with minimal anthropogenic emission sources. Both sites measure under identical conditions and instrumentation.

The PM25_valid column indicates successful validation of the measurement by the instrument's quality control system; a True value confirms the reading passed automated quality checks (sensor response time, detection range verification, baseline drift assessment). Invalid measurements due to sensor malfunction or environmental interference are marked as False.

Additional environmental variables (Temperature_C, Humidity_percent) are recorded as potential confounders or explanatory factors for particulate concentration variation, though the primary analysis focuses on location-type comparison.

Independent unit column: Measurement_ID