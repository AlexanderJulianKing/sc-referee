# Governing protocol

## Study question

Compare `aerobic_plate_count_log_cfu_g` between the two levels of `wash_treatment` (`chlorine` and `peracetic_acid`).

## Independent experimental unit

The independent experimental unit is the production batch. The column `batch_id` carries the value that
identifies it: each batch has one distinct `batch_id` value. The wash treatment was applied at the batch level and every pack in a batch carries the wash its batch received, so the batch is the unit that was assigned to a group.

## Analysis

The analysis is a two-group comparison of `aerobic_plate_count_log_cfu_g` between the two levels of `wash_treatment`.
This protocol does not select, require, or exclude any particular statistical procedure.
