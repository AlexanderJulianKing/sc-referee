# Plant Growth Study Data

This dataset contains measurements of plant stem height under two different watering schedules. Seedlings of tomato (Solanum lycopersicum) were cultivated in a controlled greenhouse environment and assigned to either daily or weekly watering regimens. Heights were measured at the two-week mark to assess growth differences between treatments.

## Variables

- **plant_id**: Unique identifier for each plant (P001-P016)
- **watering_schedule**: Treatment assignment, either 'daily' or 'weekly' watering frequency
- **height_cm**: Stem height measurement in centimeters at day 14
- **days_elapsed**: Number of days since planting (14 for all observations)

## Data Quality

All height measurements are positive values. Plants with measurement errors were excluded from the original data collection.

Independent unit column: plant_id