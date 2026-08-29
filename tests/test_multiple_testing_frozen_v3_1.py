from __future__ import annotations

from pathlib import Path

from sc_referee.core.ids import sha256_digest


def test_frozen_v3_1_and_question_surfaces_are_byte_unchanged() -> None:
    expected = {
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v3_1.py": "sha256:2cf95b4ba52200374007969d511098571f35381bdbcff5b17f930d9a554d413e",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_record_model_v3_1.py": "sha256:7fa5d768e7c6597deb1b61d65a3ebc8bb3cf2fd30a1b5c9cafe4da3338fcd1ff",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_adapter_v3_1.py": "sha256:35e66d27410fff965a02662b020ac86cf69f5bc880a73b2f2cb07a86d822776f",
        "src/sc_referee/detectors/bounded_code_csv_multiple_testing_conflict_v3_1.py": "sha256:92657c3b6edb8bbf2a68953cbc0b7f2673a6d2e422da0c4a9bd8d4049ff2b66f",
        "src/sc_referee/scientific_checks/integration_multiple_testing_v3_1.py": "sha256:50f9bd11fb419dfdad4254154387ff92d75889d841130fad42fcf46f80ab3913",
        "src/sc_referee/scientific_checks/multiple_testing_scope_questions_v1.py": "sha256:b6d985b2481d80b174a661411887973bb5cf204b5f9003344119cd134f55a36a",
        "src/sc_referee/multiple_testing_scope_attestations_v1.py": "sha256:64e0b225f34ae22dd1dd5cc01b4bc70c96bbef1d2a51df830aab004267b8b63b",
        "evaluation/development/multitest-code-slice-v3_1/QUESTION_ORACLE.json": "sha256:8d0cda616c0cd312c78722a7f45a2a7c22d1a6f33609d217a65ebed299f1d5e0",
        "evaluation/development/multitest-code-slice-v3/FIXTURE_MATRIX.json": "sha256:ca3bc50a6f1943c15ed7a144bcf316238c4670b58ffd18d4ee6b94b936bd41f5",
        "docs/implementation/MULTITEST-CODE-SLICE-3.0-RECORD-MODEL-DESIGN-2026-08-28.md": "sha256:e950b6015198c92e7f7f16d30f901be9f131c0145e96524a22df4e33ed6ec166",
        "docs/implementation/MULTITEST-3.1-SCOPE-QUESTIONS-ATTESTATION-DESIGN-2026-08-29.md": "sha256:e25eb7d1437b27cc5182ab1e1acc153b379e30d4415eee8a51286ff03df87c0f",
    }
    assert {path: sha256_digest(Path(path).read_bytes()) for path in expected} == expected
