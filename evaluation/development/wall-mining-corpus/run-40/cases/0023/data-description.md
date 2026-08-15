## Air Quality Dataset: PM2.5 Monitoring

This dataset contains 24 monthly measurements of fine particulate matter (PM2.5) concentrations collected at a regional air quality monitoring station from January 2025 through December 2026.

**Variables:**
- `date`: Measurement date (YYYY-MM-DD format, 15th of each month)
- `pm25_concentration`: PM2.5 concentration in micrograms per cubic meter (μg/m³)
- `collection_method`: Either gravimetric (reference method) or nephelometer (optical method)
- `data_quality`: Validity flag (all marked as "valid")

**Context:**
PM2.5 refers to fine inhalable particles with diameters 2.5 micrometers or smaller. The dataset captures typical seasonal variation (higher in winter due to atmospheric conditions and heating; lower in summer). Measurements use two complementary methods: gravimetric analysis (laboratory-based, highly accurate) and nephelometer (real-time optical measurement). Data quality is maintained throughout with no missing values or anomalies requiring flagging.