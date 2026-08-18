# sc-referee experimental Slice B report

Input snapshot: sha256:6fdd01fe4e8cb3edce6f0f7e0bed5bf46fdd6609d17f0e2b60ae2c5ddaa27828
Input CSV bytes: sha256:743bb4994038c4e95126307c9d5f278d9024035955ae46aab7fc0ffb451d9abf

## Findings
None.

## Conditional concerns
None.

## Material questions
- Evidence grade: MATERIAL QUESTION. Question sha256:df5b86dec8153112aced261d098be348c447148fc56f56b6362cdd238ce302f9; review-scope selection sha256:dde3815095f6b4b072d3f2e6ffe85b4478808689babb6f04addfc68a7d800652. The intake-selected audit-scope CSV has 4 verified data rows. Column C1 has 2 distinct byte values; 2 values occur in multiple rows, and 2 values occur with more than one distinct value of column C2. Does the analysis under review use this CSV? If yes, does C1 identify the scientific unit? If yes, does the scientific conclusion rely on a comparison organized by C2? If yes, does that comparison account for rows sharing one C1 value as dependent observations?
  Answer form: analysis uses selected CSV yes/no/unknown; C1 is scientific unit yes/no/unknown/not-applicable; scientific conclusion relies on C2 comparison yes/no/unknown/not-applicable; comparison accounts for shared-C1 dependence yes/no/unknown/not-applicable.
  Why material: answers determine whether this selected CSV pattern is irrelevant to the scientific conclusion, resolved by dependence-aware treatment, or remains unresolved for conclusion support.
  Basis observations: sha256:6c64c2d85d28c74e5a2cac58e58a4d49bf382c7b07c2ba9ecf92dde53e296c12; sha256:ac6e153a33f2bca1ae5a4bf69c029dd205bf128f1353fa4e3b9dad989728c09f; sha256:6e278be1d385d14e18ad8bcf2b6b4fe24a34cf502dce3eeb7de2492d4029e636; sha256:7cf870b9a129539fcd09b847a9c81a52e07c67862ea9dd54becf22f5eed16239.

## Disclosures
None.

## Coverage
- Evidence grade: COVERAGE LIMIT. Slice B does not assess repository-wide inventory completeness or whether the selected audit-scope CSV is used by an analysis.

## Observation appendix
- Evidence grade: VERIFIED OBSERVATION. Type csv-table-shape-v1; observation sha256:6c64c2d85d28c74e5a2cac58e58a4d49bf382c7b07c2ba9ecf92dde53e296c12; content sha256:743bb4994038c4e95126307c9d5f278d9024035955ae46aab7fc0ffb451d9abf; data rows 4; columns 3.
- Evidence grade: VERIFIED OBSERVATION. Type csv-selected-cardinalities-v1; observation sha256:ac6e153a33f2bca1ae5a4bf69c029dd205bf128f1353fa4e3b9dad989728c09f; content sha256:743bb4994038c4e95126307c9d5f278d9024035955ae46aab7fc0ffb451d9abf; candidate column C1; candidate distinct 2; comparison column C2; comparison distinct 2.
- Evidence grade: VERIFIED OBSERVATION. Type csv-comparison-group-sizes-v1; observation sha256:6e278be1d385d14e18ad8bcf2b6b4fe24a34cf502dce3eeb7de2492d4029e636; content sha256:743bb4994038c4e95126307c9d5f278d9024035955ae46aab7fc0ffb451d9abf; comparison column C2; sorted group sizes [2,2].
- Evidence grade: VERIFIED OBSERVATION. Type csv-unit-comparison-incidence-v1; observation sha256:7cf870b9a129539fcd09b847a9c81a52e07c67862ea9dd54becf22f5eed16239; content sha256:743bb4994038c4e95126307c9d5f278d9024035955ae46aab7fc0ffb451d9abf; candidate column C1; comparison column C2; repeated candidate values 2; cross-comparison candidate values 2; comparison-values-per-candidate histogram [[2,2]].
