# Soiling-Induced Power Loss in Coated and Bare Photovoltaic Modules

## Data

Field trial at one utility-scale array: 12 modules (6 treated with the nanocoat
anti-soiling layer, 6 bare controls) were inspected once per week for 5
consecutive weeks, yielding 60 inspection records. The response variable is
the soiling-induced power loss relative to a clean-module reference, in percent.

## Per-module mean power loss

| module_id | coating | inspections | mean loss (%) |
| --- | --- | --- | --- |
| PV-C01 | nanocoat | 5 | 1.600 |
| PV-C02 | nanocoat | 5 | 1.800 |
| PV-C03 | nanocoat | 5 | 2.000 |
| PV-C04 | nanocoat | 5 | 2.100 |
| PV-C05 | nanocoat | 5 | 2.300 |
| PV-C06 | nanocoat | 5 | 2.200 |
| PV-U01 | bare | 5 | 4.500 |
| PV-U02 | bare | 5 | 4.800 |
| PV-U03 | bare | 5 | 5.100 |
| PV-U04 | bare | 5 | 5.000 |
| PV-U05 | bare | 5 | 5.400 |
| PV-U06 | bare | 5 | 5.200 |

## Group summary

| coating | inspection records | mean (%) | SD (%) |
| --- | --- | --- | --- |
| nanocoat | 30 | 2.000 | 0.251 |
| bare | 30 | 5.000 | 0.301 |

## Test

Two-sample Student t-test (equal variances assumed) comparing nanocoat against
bare power-loss values, with each of the 60 inspection records entered as one
independent observation.

- Mean difference (nanocoat minus bare): -3.000 percentage points
- t(58) = -41.994, p < 0.001

[selected-result] Two-sample Student t-test over 60 weekly inspection records: nanocoat modules averaged 2.000% soiling power loss versus 5.000% for bare modules, a difference of -3.000 percentage points (t(58) = -41.994, p < 0.001).
