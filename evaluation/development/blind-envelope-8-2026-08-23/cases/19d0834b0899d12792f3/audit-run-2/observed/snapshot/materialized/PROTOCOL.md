# Governing protocol

## Study question

Compare `thickness_mm` between the two levels of `treatment_arm` (`active` and `vehicle`).

## Independent experimental unit

The independent experimental unit is the patient. The column `patient_id` carries the value that
identifies it: each patient has one distinct `patient_id` value. Each patient was randomised as a whole to one arm and contributed four measured target plaques carrying that arm label, so the patient is the unit that was assigned to a group.

## Analysis

The analysis is a two-group comparison of `thickness_mm` between the two levels of `treatment_arm`.
This protocol does not select, require, or exclude any particular statistical procedure.
