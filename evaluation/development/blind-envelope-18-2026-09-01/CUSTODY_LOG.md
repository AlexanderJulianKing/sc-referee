# Custody log, envelope 18 (Fable, custodian under executive authority)

Class-pure multiple testing. Detector under test: code_csv_multiple_testing 3.4.0 (development
lane); the exact repo commit is recorded below at audit time, because the authoring stages
(briefing, prompts, data, contracts, analyses, blind review) are detector-independent and were run
in parallel with the 3.4 merge gate.
briefing sha256 f3f6e47b91f69a511db5120d8a14a713ac82dbb0d719034349338e3cf8d40aa6 (11,435 B),
frozen before the prompt author was commissioned; excludes all envelope 1-17 domains; silent on
assumption checks. External-staging custody per E11-E17 protocol
(~/Desktop/random_stuff/sc-referee-blind-envelope-18-2026-09-01/).

Promotion window: E17 (4/6) + E18 >= 7/12, so E18 needs >= 3/6.

Prompt author (isolated) commissioned 2026-09-01.

Prompt author delivered; fifteen digests verified against manifest.json (PASS). ROLE_MAP.json
sealed read-only (case_roles_in_fixed_order, secrets.token_hex ids); role-map digest
cd830c2a79ea80f4fe310d8db09893b29c74fdf25d33975c713d9161feff3d92. PROMPT.txt staged read-only
per case before data authors were commissioned; custodian did not read prompt contents.

step5 (in progress): fifteen isolated data authors commissioned.
