## Paint Adhesion Testing Dataset

This dataset contains results from paint adhesion testing using the ASTM D3359 crosshatch test method. The study evaluates the performance of paint systems applied to steel substrates under controlled conditions.

### Variables

- **batch_id**: Unique identifier for each test sample (27 batches total)
- **surface_prep**: Pre-application surface preparation method (sanded, primed, or untreated)
- **environment**: Environmental exposure condition during testing (dry, humid, or salt_spray)
- **adhesion_score**: Measured adhesion strength on a 0–100 scale (higher indicates better performance)
- **application_temp_c**: Temperature in Celsius during paint application
- **days_to_test**: Duration of environmental exposure before adhesion testing

### Study Design

Three surface preparation methods were tested across three environmental conditions with three replicates per combination (3×3×3 factorial design). All samples were cured for 14 days before exposure testing began. Application temperatures were controlled within 21–23°C range to minimize thermal effects on results. This dataset is typical of quality control testing in coating applications and manufacturing.