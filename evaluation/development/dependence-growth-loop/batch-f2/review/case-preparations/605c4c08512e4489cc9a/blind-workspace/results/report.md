# Nest-site choice in field-collected Temnothorax rugatulus colonies

## Design

Each colony in this survey was collected from its own granite outcrop, at
least fifty metres from the next, and was released into the two-cavity arena
exactly once. One row of the data table is therefore one colony and one
trial: no colony was retested, and no colony contributes a second choice.

## Analysis

Exact two-sided binomial test (scipy.stats.binomtest) on the number of
colonies that emigrated into the shaded cavity, against the no-preference
expectation of 0.5.

## Numbers

- Colonies assayed: 24
- Emigrated to the shaded cavity: 19
- Emigrated to the exposed cavity: 5
- Observed proportion choosing shaded: 0.7917
- Null proportion: 0.5
- Exact two-sided p-value: 0.00661

[selected-result] Exact two-sided binomial test on 24 independent colonies: 19 of 24 (proportion 0.7917) chose the shaded cavity against a null of 0.5, p = 0.00661, so the no-preference null is rejected at alpha = 0.05.

## Reading

The bias toward the dim cavity is strong and unlikely under indifference. The
count that enters the test is a count of separate colonies, so the exact
binomial sampling model matches the way the data were collected.
