from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _run_isolated(project_root: Path, body: str) -> dict[str, Any]:
    package_root = project_root / "evaluation" / "src"
    core_root = project_root / "src"
    script = f"""
import sys
sys.path[:0] = [{str(package_root)!r}, {str(core_root)!r}]
{body}
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    return json.loads(completed.stdout)


def test_target_worker_import_has_exact_distribution_closure(project_root: Path) -> None:
    result = _run_isolated(
        project_root,
        """
import importlib.metadata
import json
baseline_modules = set(sys.modules)
import sc_referee_evaluation.selected_result_qualification_target_worker

package_distributions = importlib.metadata.packages_distributions()
distributions = sorted(
    {
        distribution
        for module_name in set(sys.modules) - baseline_modules
        for distribution in package_distributions.get(module_name.partition('.')[0], ())
    },
    key=str.casefold,
)
evaluation_modules = sorted(
    module_name
    for module_name in sys.modules
    if module_name == 'sc_referee_evaluation'
    or module_name.startswith('sc_referee_evaluation.')
)
print(json.dumps({
    'distributions': distributions,
    'evaluation_modules': evaluation_modules,
}))
""",
    )

    assert result == {
        "distributions": ["sc-referee", "sc-referee-evaluation"],
        "evaluation_modules": [
            "sc_referee_evaluation",
            "sc_referee_evaluation.prospective_selected_result_verifier",
            "sc_referee_evaluation.selected_result_qualification_target_worker",
        ],
    }


def test_lazy_package_preserves_all_public_exports(project_root: Path) -> None:
    result = _run_isolated(
        project_root,
        """
import json
import sc_referee_evaluation as evaluation

initial_modules = sorted(
    module_name
    for module_name in sys.modules
    if module_name == 'sc_referee_evaluation'
    or module_name.startswith('sc_referee_evaluation.')
)
namespace = {}
exec('from sc_referee_evaluation import *', namespace)
star_exports = sorted(name for name in namespace if name != '__builtins__')
print(json.dumps({
    'initial_modules': initial_modules,
    'all_is_unique': len(evaluation.__all__) == len(set(evaluation.__all__)),
    'star_exports': star_exports,
    'declared_exports': sorted(evaluation.__all__),
    'aliases': {
        'derivation': evaluation.SELECTED_RESULT_DERIVATION_VERSION,
        'validation': evaluation.SELECTED_RESULT_VALIDATION_VERSION,
        'verifier': evaluation.SELECTED_RESULT_VERIFIER_VERSION,
        'protocol': evaluation.PROSPECTIVE_QUALIFICATION_PROTOCOL_VERSION,
    },
}))
""",
    )

    assert result["initial_modules"] == ["sc_referee_evaluation"]
    assert result["all_is_unique"] is True
    assert result["star_exports"] == result["declared_exports"]
    assert result["aliases"] == {
        "derivation": "1.0.0",
        "protocol": "1.0.0",
        "validation": "1.0.0",
        "verifier": "1.0.0",
    }
