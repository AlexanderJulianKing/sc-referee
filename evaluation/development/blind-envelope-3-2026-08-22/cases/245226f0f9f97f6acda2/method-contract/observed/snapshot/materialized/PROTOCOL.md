# Governing protocol

## Study question

Compare `tumour_volume_mm3` between the two levels of `treatment_group` (`vehicle` and `treated`).

## Independent experimental unit

The independent experimental unit is the animal. The column `animal_id` carries the value that
identifies it: each animal has one distinct `animal_id` value. Treatment was assigned at the level of the animal, so the animal is the unit that was assigned to a group.

## Analysis

The analysis is a two-group comparison of `tumour_volume_mm3` between the two levels of `treatment_group`.
This protocol does not select, require, or exclude any particular statistical procedure.
