# Dependence growth-9 frozen-corpus re-measure

Date: 2026-08-15  
Baseline: committed growth-8 `e356345`  
Corpus: all 83 materialized cases in batches A through I2  
Result: 29 reason-set movements; zero outcome-class movements; accusations `0 -> 0`

All moved cases remained `unsupported`. Unlisted cases retained their exact
sorted reason sets.

| Batch | Case | Growth-8 reasons | Growth-9 reasons |
| --- | --- | --- | --- |
| B | `8b01b6d08e58aa5cce6f` | `function-globals-read` | `raise-guard-not-modeled` |
| B | `bf08b2218ca9cef1db2d` | `count-predicate-not-closed`; `function-globals-read` | `count-predicate-not-closed`; `raise-guard-not-modeled` |
| C | `41cfd59360a1ca24ca4b` | `function-globals-read`; `function-return-shape` | `function-return-shape`; `raise-guard-not-modeled` |
| D | `7da68ec265e1bb2f6640` | `function-globals-read` | `raise-guard-not-modeled` |
| E1 | `47b6fb6bf1d4fbcefd7c` | `function-argument-not-simple` | `reader-form-unsupported` |
| E1 | `7afb4508b0d957f51ca7` | `function-globals-read`; `function-return-shape` | `function-return-shape` |
| E1 | `acea1e7265fd2ac91a43` | `function-globals-read` | `function-globals-read`; `raise-guard-not-modeled` |
| E1 | `f203d7292f9530cbdf48` | `function-globals-read` | `raise-guard-not-modeled` |
| E2 | `102f7842bc112abba84f` | `function-globals-read` | `raise-guard-not-modeled` |
| E2 | `128c2bd7128bc67b5964` | `function-globals-read` | `function-argument-not-simple` |
| E2 | `18f0af8326d59d579c43` | `function-globals-read`; `function-return-shape` | `function-return-shape`; `raise-guard-not-modeled` |
| E2 | `e57e3c73264eda49b3cc` | `function-globals-read` | `raise-guard-not-modeled` |
| F1 | `c2db115846830b7d908c` | `function-globals-read` | `raise-guard-not-modeled` |
| F1 | `f68415be40b9234987de` | `function-globals-read` | `raise-guard-not-modeled` |
| F2 | `605c4c08512e4489cc9a` | `count-predicate-not-closed`; `function-globals-read` | `count-predicate-not-closed`; `raise-guard-not-modeled` |
| F2 | `b24355b160cf4665b929` | `function-globals-read` | `raise-guard-not-modeled` |
| G1 | `2ddf508d135fd7fce5df` | `function-globals-read` | `raise-guard-not-modeled` |
| G1 | `8b55946a92793ebcd387` | `function-globals-read`; `function-return-shape` | `function-return-shape` |
| G2 | `a8b660a9685f13f0187f` | `function-globals-read` | `raise-guard-not-modeled` |
| H1 | `d8e451762e6f79802f9f` | `function-globals-read` | `function-argument-not-simple` |
| H2 | `4da6848cdd3a5d975d87` | `count-predicate-not-closed`; `function-globals-read`; `function-return-shape` | `count-predicate-not-closed`; `function-return-shape`; `raise-guard-not-modeled` |
| H2 | `78bfad17cf5492340eb0` | `function-default-params`; `function-globals-read`; `function-return-shape` | `function-default-params`; `function-return-shape`; `raise-guard-not-modeled` |
| I1 | `125813c0f228fcecd435` | `function-globals-read` | `raise-guard-not-modeled` |
| I1 | `724ad079fa57acb93f8a` | `module-constant-not-closed` | `import-use-outside-grammar` |
| I1 | `ce7daed01bb0fa178e26` | `function-argument-not-simple` | `procedure-call-unresolved` |
| I2 | `1469a50a5381493a261b` | `function-globals-read` | `group-accumulator-not-total` |
| I2 | `256ce9b8dd475ee95a97` | `function-globals-read` | `count-domain-not-row-bound` |
| I2 | `5f4ec238d04074266e32` | `function-argument-not-simple` | `reader-form-unsupported` |
| I2 | `6aac19a2a2aa18f85740` | `function-globals-read` | `raise-guard-not-modeled` |

The `ce7daed01bb0fa178e26` ordering conflict is recorded in
`SCHEMA_GAP_REGISTER.md`; the dedicated amended container probes reach and pin
`sink-aliases-operand-object` without widening procedure-result grammar.
