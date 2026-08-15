## Equipment Failure Time Data

This dataset contains operating hours until failure for 20 centrifugal pump units deployed in industrial water treatment facilities. Each pump operates continuously under standardized conditions until mechanical failure occurs.

### Data Variables

- **equipment_id**: Unique pump identifier (PUMP-001 through PUMP-020)
- **failure_hours**: Cumulative operating hours from installation to failure, measured by equipment runtime meter

### Collection Context

The records were extracted from maintenance logs spanning 3 years of operation. All pumps are identical models installed with similar flow requirements and environmental conditions. No pumps were censored; all represent complete failure observations.

### Statistical Properties

- Sample size: 20 units
- Range: 245 to 1,523 operating hours
- Application domain: Industrial water treatment, recirculation systems
- Measurement precision: 1-hour resolution

### Data Quality

No missing values. All times are direct observations from equipment instrumentation. No adjustments for startup/shutdown periods were applied.