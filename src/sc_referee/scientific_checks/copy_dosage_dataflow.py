"""ADR-0069 static dataflow resolution of the copy-dosage exposure representation.

This library works backward from the fitted model whose output reaches the
written report. It reads each Python workflow source statically, tags the
provenance of every value read from a staged input, and tracks, per value,
whether the number reaching the model's exposure operand still lives on a
continuous scale or has been mapped onto a finite set of literal values.
Variable names, column names, and report nouns never matter; only the
operations do.

The tag lattice has four states. ``continuous`` is a value this library has
positively established as real-valued. ``quantized`` is a value it has
positively established as confined to a finite set of literal values, either
because a recognized quantizing operation produced it or because it was
parsed as an integer from staged text. ``text`` is an unparsed staged
string. ``opaque`` is everything else. A quantizing operation is a map onto a
finite set of literal values, or a float-to-integer rounding or truncation;
``int(x)`` over a float-provenance value quantizes, while ``int(x)`` over
staged text is a parse and establishes integer coding instead.

The cardinal rule: ``continuous`` is never a fallthrough. An unreadable step
on the path into the exposure operand abstains, because an operation this
library cannot read may be exactly the rounding whose presence the frozen
method contract forbids.

v2.0.1 closes nine wrong-answer families a second adversarial review
demonstrated. Four of them changed a rule rather than an enumeration:

- Arithmetic no longer restores the continuous scale from a value that
  descends from the same traced source as the value being repaired. Every
  traced value carries a provenance-id set, and arithmetic over two traced
  values whose id sets intersect is unreadable. ``x - x % 1`` is
  ``floor(x)``, ``x + (round(x) - x)`` is ``round(x)``, and both read as
  continuous under a rule that only compares tags. Restoration survives only
  for a genuinely independent continuous operand.
- Calls are default-deny for mutation. Any call outside the modelled
  vocabulary whose subtree names a traced value invalidates that value's
  whole alias group, as does any ``out=`` target. ``numpy.copyto``,
  ``out=``, ``.fill``, ``.put`` and their kin are covered by the default
  rather than by extending a list of known mutators.
- A literal lookup table is a binning, whatever its values are. Three bin
  centres are three levels, so ``centers[index]``, ``cut`` labels, a literal
  ``.map`` dictionary, and literal ``numpy.where`` branches all read as
  quantized; a literal table never re-expands a quantized value.
- Imports are hermetic. A document the parser did not parse, an import that
  resolves to another document in the same case, a relative or star import,
  and an import outside the modelled analysis stack all leave the case
  unsupported, because what such a module does on import is outside this
  trace.

Soundness rules (each backed by a demonstrated counterexample in
``tests/test_copy_dosage_soundness.py``):

- An unrecognized operation on the exposure path abstains; it never reads as
  the continuous representation.
- A quantizer followed by arithmetic against an independently traced
  continuous value restores the continuous scale; the classification traces
  the whole chain rather than firing because a quantizer exists somewhere in
  the document. Arithmetic against a value descended from the same source
  restores nothing and abstains.
- A quantization that only reaches a written table, while the continuous
  value feeds the model, classifies as continuous.
- Only a model fit whose result can reach the written report classifies. A
  report write counts only when its receiver is a filesystem path, and a
  return statement seeds the report only from a function some reachable
  caller actually calls.
- The exposure operand of a multi-regressor fit must be uniquely
  identifiable from provenance: the single non-constant regressor whose
  value descends from a recognized estimator output, or, when no estimator
  produced any regressor, the single non-constant regressor that is a staged
  column with established integer coding and an unchanged path into the fit.
  Zero or more than one such regressor abstains.
- An estimator's category is read from its constructor call, never from the
  name of the variable holding it; an estimator whose construction this
  library never saw is opaque, so ``predict`` and ``predict_proba`` on it
  abstain.
- Names that alias one runtime object share an invalidation group: mutating
  any member drops the provenance of every member. A container literal
  holding a traced value joins that value's group, so mutation reached
  through the container is mutation of the value. Any assignment form the
  environment model does not fully handle, touching any tagged name, leaves
  the document unsupported.
- A local helper called with a traced table or array is simulated for its
  side effects, and the parameters it mutates in place are written back to
  the caller's binding; a helper whose body this trace cannot complete
  invalidates its traced arguments instead.
- A local function definition shadows the built-in vocabulary, and a
  callable name that is rebound anywhere is opaque everywhere.
- Fits reaching the report with conflicting classifications abstain.
- Helper tracing is depth-bounded with cycle detection, and expression
  tracing carries its own depth bound; recursion abstains instead of
  crashing.
- A function body is traced with its parameters masked, so an exposure
  operand arriving as a parameter abstains rather than letting a module
  global stand in for it.

The report-reaching closure, the statement flattening, the ``__main__``
guard recognition, the alias-group model, the call-binding shape, and the
evidence-span projection are modelled on ``founder_orientation_dataflow``;
they are copied rather than imported so the two recognizers stay
independently versionable and neither module's identity moves when the other
changes.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass, field, replace
from itertools import count
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.scientific_checks.core import (
    EvidenceSpan,
    FrozenInspectionContext,
    InspectionDocument,
)

COPY_DOSAGE_DATAFLOW_IMPLEMENTATION_DIGEST = sha256_digest(Path(__file__).read_bytes())

_MAX_CALL_DEPTH = 2
_MAX_EXPRESSION_DEPTH = 100
# An integer literal wider than this is not a quantity this trace reads. It is
# discarded rather than converted, because ``float()`` of a large enough
# integer raises instead of returning a number.
_MAX_LITERAL_MAGNITUDE = 10**12

# Provenance identity. Every traced value carries the set of source values it
# descends from, so arithmetic can tell an independent operand from the value
# it is supposedly repairing.
_PROVENANCE_COUNTER = count()


def _fresh_ids() -> frozenset[int]:
    """A provenance id for one newly created traced value."""

    return frozenset({next(_PROVENANCE_COUNTER)})


# ---------------------------------------------------------------------------
# The tag lattice.

_CONTINUOUS = "continuous"
_QUANTIZED = "quantized"
_TEXT = "text"
_OPAQUE_TAG = "opaque"

# Provenance origins. Everything in _MODEL_ORIGINS descends from a recognized
# estimator output, which is what makes a regressor a copy-dosage candidate.
_ORIGIN_PROBABILITIES = "class_probabilities"
_ORIGIN_EXPECTATION_TERMS = "posterior_expectation_terms"
_ORIGIN_EXPECTATION = "posterior_expectation"
_ORIGIN_CALIBRATION = "direct_calibration"
_ORIGIN_HARD_CALL = "classifier_hard_call"
# A dose-shaped step this library cannot read. It counts as a model origin so
# that a regressor carrying it is a candidate exposure operand; its opaque tag
# then abstains for the document rather than letting a readable sibling
# regressor answer in its place.
_ORIGIN_UNREADABLE = "unreadable_copy_model_step"
_MODEL_ORIGINS = frozenset(
    {
        _ORIGIN_PROBABILITIES,
        _ORIGIN_EXPECTATION_TERMS,
        _ORIGIN_EXPECTATION,
        _ORIGIN_CALIBRATION,
        _ORIGIN_HARD_CALL,
        _ORIGIN_UNREADABLE,
    }
)

# The three classifications this library can reach.
_STATE_QUANTIZED = "integer_hard_state"
_STATE_EXPECTATION = "posterior_expectation"
_STATE_CALIBRATION = "direct_calibration"

# ---------------------------------------------------------------------------
# Library vocabulary. Every entry names a public library API whose semantics,
# not whose spelling, decides the tag.

_STAGED_FRAME_CALLS = frozenset(
    {
        "pandas.read_csv",
        "pandas.read_table",
        "pandas.read_excel",
        "pandas.read_parquet",
        "pandas.read_feather",
        "pandas.read_stata",
        "pandas.read_sas",
        "pandas.read_json",
        "pandas.read_hdf",
    }
)
_STAGED_ROW_CALLS = frozenset({"csv.DictReader", "csv.reader"})
_PATH_CALLS = frozenset({"Path", "pathlib.Path", "PurePath", "pathlib.PurePath"})
_WRITE_METHODS = frozenset({"write", "writelines", "write_text", "to_csv", "to_markdown"})
_MUTATING_METHODS = frozenset(
    {
        "append",
        "extend",
        "insert",
        "pop",
        "remove",
        "clear",
        "update",
        "setdefault",
        "sort",
        "reverse",
        "popitem",
    }
)

# Importing a module executes it. Only the analysis stack this library models
# may be imported; anything else -- including a relative import, which
# resolves inside a package this trace cannot see -- leaves the document
# unsupported. This is deliberately not the founder module's stdlib-only
# allowlist: reading numpy, pandas, and the estimator libraries is this
# recognizer's whole job.
_ALLOWED_IMPORT_MODULES = frozenset(
    {
        "csv",
        "decimal",
        "fractions",
        "io",
        "math",
        "numpy",
        "pandas",
        "pathlib",
        "patsy",
        "scipy",
        "sklearn",
        "statistics",
        "statsmodels",
    }
)

_INTEGER_DTYPES = frozenset(
    {
        "int",
        "int_",
        "intp",
        "intc",
        "int8",
        "int16",
        "int32",
        "int64",
        "uint",
        "uint8",
        "uint16",
        "uint32",
        "uint64",
        "long",
        "i1",
        "i2",
        "i4",
        "i8",
        "u1",
        "u2",
        "u4",
        "u8",
        "Int8",
        "Int16",
        "Int32",
        "Int64",
        "bool",
        "bool_",
        "?",
    }
)
_FLOAT_DTYPES = frozenset(
    {
        "float",
        "float_",
        "float16",
        "float32",
        "float64",
        "double",
        "f2",
        "f4",
        "f8",
        "Float32",
        "Float64",
    }
)

# Rounding and truncation: every one of these lands on the integers.
_ROUNDING_CALLS = frozenset(
    {
        "numpy.round",
        "numpy.around",
        "numpy.rint",
        "numpy.floor",
        "numpy.ceil",
        "numpy.trunc",
        "numpy.fix",
        "math.floor",
        "math.ceil",
        "math.trunc",
    }
)
_ROUNDING_METHODS = frozenset({"round", "rint", "floor", "ceil", "trunc"})
# Binning and ranking: every one of these lands on a finite index set.
_BINNING_CALLS = frozenset(
    {
        "numpy.digitize",
        "numpy.searchsorted",
        "numpy.argmax",
        "numpy.argmin",
        "numpy.argsort",
        "numpy.nonzero",
        "numpy.bincount",
    }
)
_BINNING_METHODS = frozenset({"argmax", "argmin", "idxmax", "idxmin", "searchsorted", "digitize"})
_TABLE_CALLS = frozenset({"pandas.cut", "pandas.qcut"})
_SHAPE_METHODS = frozenset({"reshape", "ravel", "flatten", "squeeze", "to_numpy", "copy"})
_SHAPE_ATTRIBUTES = frozenset({"values", "T"})
_AGGREGATE_METHODS = frozenset({"sum", "mean", "nansum"})
_PREDICTION_METHODS = frozenset({"predict", "predict_proba", "predict_log_proba"})
_PRESERVING_CALLS = frozenset(
    {
        "numpy.clip",
        "numpy.abs",
        "numpy.absolute",
        "numpy.nan_to_num",
        "numpy.ravel",
        "numpy.reshape",
        "numpy.squeeze",
        "numpy.copy",
        "numpy.asarray_chkfinite",
    }
)
_BUILTIN_CALLS = frozenset(
    {"int", "float", "round", "list", "len", "sum", "abs", "max", "min", "tuple", "str"}
)

_DESIGN_CALLS = frozenset({"numpy.column_stack", "numpy.stack", "numpy.hstack", "numpy.vstack"})
_CONSTANT_CALLS = frozenset(
    {
        "statsmodels.api.add_constant",
        "statsmodels.tools.add_constant",
        "statsmodels.tools.tools.add_constant",
    }
)

_CLASSIFIER_CONSTRUCTORS = frozenset(
    {
        "sklearn.linear_model.LogisticRegression",
        "sklearn.linear_model.LogisticRegressionCV",
        "sklearn.linear_model.RidgeClassifier",
        "sklearn.linear_model.RidgeClassifierCV",
        "sklearn.linear_model.SGDClassifier",
        "sklearn.linear_model.Perceptron",
        "sklearn.ensemble.RandomForestClassifier",
        "sklearn.ensemble.ExtraTreesClassifier",
        "sklearn.ensemble.GradientBoostingClassifier",
        "sklearn.ensemble.HistGradientBoostingClassifier",
        "sklearn.ensemble.AdaBoostClassifier",
        "sklearn.ensemble.BaggingClassifier",
        "sklearn.tree.DecisionTreeClassifier",
        "sklearn.neighbors.KNeighborsClassifier",
        "sklearn.svm.SVC",
        "sklearn.svm.LinearSVC",
        "sklearn.naive_bayes.GaussianNB",
        "sklearn.naive_bayes.MultinomialNB",
        "sklearn.discriminant_analysis.LinearDiscriminantAnalysis",
        "sklearn.discriminant_analysis.QuadraticDiscriminantAnalysis",
        "sklearn.neural_network.MLPClassifier",
        "sklearn.calibration.CalibratedClassifierCV",
        "xgboost.XGBClassifier",
        "lightgbm.LGBMClassifier",
    }
)
_CONTINUOUS_CONSTRUCTORS = frozenset(
    {
        "sklearn.linear_model.LinearRegression",
        "sklearn.linear_model.Ridge",
        "sklearn.linear_model.RidgeCV",
        "sklearn.linear_model.Lasso",
        "sklearn.linear_model.LassoCV",
        "sklearn.linear_model.ElasticNet",
        "sklearn.linear_model.ElasticNetCV",
        "sklearn.linear_model.BayesianRidge",
        "sklearn.linear_model.ARDRegression",
        "sklearn.linear_model.HuberRegressor",
        "sklearn.linear_model.SGDRegressor",
        "sklearn.linear_model.TheilSenRegressor",
        "sklearn.ensemble.RandomForestRegressor",
        "sklearn.ensemble.ExtraTreesRegressor",
        "sklearn.ensemble.GradientBoostingRegressor",
        "sklearn.ensemble.HistGradientBoostingRegressor",
        "sklearn.tree.DecisionTreeRegressor",
        "sklearn.neighbors.KNeighborsRegressor",
        "sklearn.svm.SVR",
        "sklearn.neural_network.MLPRegressor",
        "sklearn.cross_decomposition.PLSRegression",
        "sklearn.isotonic.IsotonicRegression",
        "sklearn.kernel_ridge.KernelRidge",
        "xgboost.XGBRegressor",
        "lightgbm.LGBMRegressor",
    }
)
# Estimator wrappers whose fitted terminal stage this trace cannot read.
_OPAQUE_ESTIMATOR_CONSTRUCTORS = frozenset(
    {
        "sklearn.pipeline.Pipeline",
        "sklearn.pipeline.make_pipeline",
        "sklearn.model_selection.GridSearchCV",
        "sklearn.model_selection.RandomizedSearchCV",
        "sklearn.multiclass.OneVsRestClassifier",
        "sklearn.compose.TransformedTargetRegressor",
    }
)

# Statsmodels model constructors, with the position of their exog argument.
_MODEL_CONSTRUCTORS: dict[str, int] = {
    "statsmodels.api.OLS": 1,
    "statsmodels.api.WLS": 1,
    "statsmodels.api.GLS": 1,
    "statsmodels.api.GLSAR": 1,
    "statsmodels.api.GLM": 1,
    "statsmodels.api.Logit": 1,
    "statsmodels.api.Probit": 1,
    "statsmodels.api.Poisson": 1,
    "statsmodels.api.NegativeBinomial": 1,
    "statsmodels.api.MNLogit": 1,
    "statsmodels.api.OrderedModel": 1,
    "statsmodels.api.RLM": 1,
    "statsmodels.api.QuantReg": 1,
    "statsmodels.api.MixedLM": 1,
    "statsmodels.api.GEE": 1,
    "statsmodels.api.PHReg": 1,
    "statsmodels.regression.linear_model.OLS": 1,
    "statsmodels.regression.linear_model.WLS": 1,
    "statsmodels.regression.linear_model.GLS": 1,
    "statsmodels.discrete.discrete_model.Logit": 1,
    "statsmodels.discrete.discrete_model.Poisson": 1,
    "statsmodels.genmod.generalized_linear_model.GLM": 1,
}

# Every call whose effect on a traced value this library models. A call outside
# this vocabulary is presumed to mutate whatever traced value its subtree
# names: that is the only posture under which ``numpy.copyto``, ``.fill``,
# ``.put``, ``.itemset``, ``.resize`` and every future in-place API are covered
# without enumerating them.
_RECOGNIZED_CALL_PATHS = (
    _STAGED_FRAME_CALLS
    | _STAGED_ROW_CALLS
    | _CLASSIFIER_CONSTRUCTORS
    | _CONTINUOUS_CONSTRUCTORS
    | _OPAQUE_ESTIMATOR_CONSTRUCTORS
    | frozenset(_MODEL_CONSTRUCTORS)
    | _CONSTANT_CALLS
    | _DESIGN_CALLS
    | _PRESERVING_CALLS
    | _ROUNDING_CALLS
    | _BINNING_CALLS
    | _TABLE_CALLS
    | frozenset({"pandas.DataFrame"})
    | frozenset({"numpy.array", "numpy.asarray", "numpy.asfarray"})
    | frozenset({"numpy.where"})
    | frozenset({"numpy.sum", "numpy.nansum", "numpy.mean"})
    | frozenset({"numpy.dot", "numpy.matmul", "numpy.inner"})
    | frozenset(f"builtins.{name}" for name in _BUILTIN_CALLS)
)
_RECOGNIZED_METHODS = (
    _ROUNDING_METHODS
    | _BINNING_METHODS
    | _SHAPE_METHODS
    | _AGGREGATE_METHODS
    | _PREDICTION_METHODS
    | frozenset({"astype", "clip", "map", "dot", "fit"})
)
# Positional out-parameters: every numpy ufunc in the recognized vocabulary
# accepts its destination array as the argument after the ones this trace
# reads, so an extra positional argument naming a traced value is a write.
_UFUNC_CALLS = _ROUNDING_CALLS | _PRESERVING_CALLS

_UNSUPPORTED_STATEMENTS = (
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.If,
    ast.With,
    ast.AsyncWith,
    ast.Try,
)


def copy_dosage_dataflow_grammar(
    hard_operand: str, expectation_operand: str, calibration_operand: str
) -> dict[str, Any]:
    return {
        "grammar_id": "copy-dosage-representation-dataflow",
        "grammar_version": "2.0.1",
        "staged_read_operations": sorted(_STAGED_FRAME_CALLS | _STAGED_ROW_CALLS),
        "tag_lattice": [_CONTINUOUS, _QUANTIZED, _TEXT, _OPAQUE_TAG],
        "quantizing_operations": [
            "round, numpy round/around/rint/floor/ceil/trunc/fix, math floor/ceil/trunc, "
            "with a literal decimal count of zero or less",
            "int() or astype of an integer dtype over a float-provenance value",
            "an integer dtype argument to numpy array/asarray or to to_numpy",
            "floor division over a float-provenance value",
            "numpy digitize, searchsorted, argmax, argmin",
            "pandas cut or qcut with a literal numeric label sequence",
            "map over a dict literal whose values are all numeric literals",
            "numpy where whose two branches are numeric literals",
            "indexing a literal sequence, whatever values it holds",
            "a comparison, whose result is a two-valued mask",
            "predict of an estimator whose constructor is a classifier",
        ],
        "parse_operations": [
            "int() or astype of an integer dtype over staged text, which establishes "
            "integer coding rather than quantizing a continuous value",
            "float() or astype of a float dtype over staged text",
        ],
        "re_expansion_operations": [
            "arithmetic between a quantized value and a traced continuous value that "
            "descends from no source the quantized value descends from",
            "a literal table never re-expands: a finite set of literal levels is a "
            "binning whether or not its values are whole numbers",
            "a float cast never re-expands a quantized value",
        ],
        "provenance_identity": (
            "every traced value carries the set of source values it descends from; "
            "arithmetic over two traced values whose sets intersect is unreadable, "
            "because the second operand can cancel exactly the information the first "
            "one lost"
        ),
        "constant_reading": (
            "a branch value, a level value, and a decimal count are read only as a "
            "numeric literal or its negation; no arithmetic over constants is folded "
            "and no call is evaluated"
        ),
        "mutation_posture": (
            "default-deny: a call outside the modelled vocabulary whose subtree names a "
            "traced value invalidates that value's whole alias group, as does any out= "
            "target or extra positional destination of a recognized ufunc; a container "
            "literal holding a traced value joins its alias group"
        ),
        "import_hygiene": (
            "a python document the parser did not parse, an import resolving to any "
            "path component or module stem of another document in the case, a relative "
            "import, a star import, and an import outside the modelled analysis stack "
            "each leave the case unsupported"
        ),
        "allowed_import_modules": sorted(_ALLOWED_IMPORT_MODULES),
        "estimator_category_source": "constructor_call_path_only",
        "classifier_constructors": sorted(_CLASSIFIER_CONSTRUCTORS),
        "continuous_constructors": sorted(_CONTINUOUS_CONSTRUCTORS),
        "opaque_estimator_constructors": sorted(_OPAQUE_ESTIMATOR_CONSTRUCTORS),
        "model_constructors": sorted(_MODEL_CONSTRUCTORS),
        "design_forms": [
            "numpy column_stack, stack, hstack, and vstack over a literal sequence",
            "statsmodels add_constant over any of the above",
            "a pandas DataFrame literal or a literal column selection",
            "a single non-constant regressor expression",
        ],
        "exposure_operand_rule": (
            "the single non-constant regressor of a report-reaching fit whose value "
            "descends from a recognized estimator output; when no regressor does, the "
            "single non-constant regressor that is a staged column with established "
            "integer coding and an unchanged path into the fit; zero or more than one "
            "abstains"
        ),
        "operand_by_tag": {
            "quantized": hard_operand,
            "continuous_from_posterior_expectation": expectation_operand,
            "continuous_from_direct_calibration": calibration_operand,
        },
        "report_reachability": (
            "a write whose receiver resolves to a filesystem path, or a return from a "
            "function some reachable caller calls"
        ),
        "control_flow": (
            "straight-line assignments, comprehensions, with-blocks, functions, and the "
            "__main__ guard; every other branch or loop leaves the document unsupported"
        ),
        "function_support": (
            "straight-line bodies whose first top-level return is the last statement; "
            "positional and keyword call binding; local definitions shadow the library "
            "vocabulary and a rebound callable name is opaque everywhere; depth-bounded "
            "with cycle detection"
        ),
        "assignment_support": (
            "single-name assignment and literal frame-column assignment only; names bound "
            "to one another, and a container literal holding a traced value, share an "
            "invalidation group, and any other assignment form touching a tagged name "
            "leaves the document unsupported"
        ),
        "soundness": [
            "continuous is never a fallthrough",
            "unrecognized exposure-path operations abstain",
            "re-expansion only by an independently traced continuous operand",
            "a literal level table is a binning, never a re-expansion",
            "unmodelled calls are presumed to mutate what they name",
            "hermetic imports, or the case is unsupported",
            "oversized literals and unparsable sources abstain instead of raising",
            "display-only quantization never classifies",
            "estimator category comes from the constructor, never a variable name",
            "an estimator whose construction was never seen is opaque",
            "aliased values share mutation invalidation",
            "unhandled assignment forms touching tagged names abstain",
            "report-reaching fit linkage",
            "non-unique exposure operands abstain",
            "conflicting classifications abstain",
            "bounded call depth with cycle abstention",
            "bounded expression-tracing depth",
        ],
        "nomenclature_authority": "none",
    }


def copy_dosage_dataflow_grammar_digest(
    hard_operand: str, expectation_operand: str, calibration_operand: str
) -> str:
    return semantic_digest(
        copy_dosage_dataflow_grammar(hard_operand, expectation_operand, calibration_operand)
    )


# ---------------------------------------------------------------------------
# Value model.


@dataclass(frozen=True)
class _Col:
    """One traced numeric value, with its lattice tag and provenance.

    ``ids`` is the set of source values this one descends from. Two values
    whose sets intersect are not independent, so arithmetic between them can
    cancel exactly the information one of them lost.
    """

    tag: str
    origin: str | None = None
    staged: bool = False
    unchanged: bool = False
    node: ast.AST | None = None
    operation: str | None = None
    ids: frozenset[int] = frozenset()

    @property
    def model_derived(self) -> bool:
        return self.origin in _MODEL_ORIGINS


def _joined_ids(*values: _Value) -> frozenset[int]:
    """The provenance every traced operand of an expression contributes."""

    joined: frozenset[int] = frozenset()
    for item in values:
        if isinstance(item, _Col):
            joined |= item.ids
    return joined


@dataclass(frozen=True)
class _Rows:
    """A row set whose per-column provenance is known relative to a staged read."""

    columns: tuple[tuple[str, _Col], ...] = ()
    default: _Col | None = None


@dataclass(frozen=True)
class _Frame:
    """A table whose per-column provenance is known only where the trace set it."""

    columns: tuple[tuple[str, _Col], ...] = ()
    default: _Col | None = None


@dataclass(frozen=True)
class _Estimator:
    category: str  # "classifier" | "continuous"


@dataclass(frozen=True)
class _Design:
    regressors: tuple[_Col, ...]


@dataclass(frozen=True)
class _Model:
    regressors: tuple[_Col, ...]


@dataclass(frozen=True)
class _Fit:
    regressors: tuple[_Col, ...]
    estimator: _Estimator | None = None


@dataclass(frozen=True)
class _Const:
    value: float


@dataclass(frozen=True)
class _Literals:
    """A literal numeric sequence.

    Its values are never read for integrality. A literal table is a finite
    set of levels however its levels are spelled, so it always bins.
    """

    values: tuple[float, ...]

    @property
    def ordered_states(self) -> bool:
        return len(self.values) >= 2 and list(self.values) == [
            float(index) for index in range(len(self.values))
        ]


@dataclass(frozen=True)
class _EmptyList:
    pass


@dataclass(frozen=True)
class _Opaque:
    pass


_OPAQUE = _Opaque()
_EMPTY_LIST = _EmptyList()

_Value = (
    _Col
    | _Rows
    | _Frame
    | _Estimator
    | _Design
    | _Model
    | _Fit
    | _Const
    | _Literals
    | _EmptyList
    | _Opaque
)

_OPAQUE_COL = _Col(_OPAQUE_TAG)


@dataclass(frozen=True)
class _Classification:
    node: ast.AST
    dose_node: ast.AST | None
    state: str
    operation: str | None


@dataclass(frozen=True)
class CopyDosageDataflowResolution:
    """The outcome of the bounded source trace across every Python document."""

    state: str  # "unique" | "none" | "ambiguous" | "unsupported"
    representation: str | None
    operand_value: str | None
    operation: str | None
    spans: tuple[EvidenceSpan, ...]
    source_path: str | None


@dataclass
class _TraceContext:
    functions: dict[str, ast.FunctionDef]
    aliases_by_path: dict[str, str] = field(default_factory=dict)
    opaque_callables: frozenset[str] = frozenset()
    path_names: frozenset[str] = frozenset()
    reaching: set[str] = field(default_factory=set)
    depth: int = 0
    expression_depth: int = 0
    visiting: set[str] = field(default_factory=set)
    unresolved: bool = False


class _Aliases:
    """Names that are known to reference one runtime object.

    A plain ``alias = frame`` binds two names to the same object, so mutating
    either one invalidates the provenance of both. Groups are per scope and
    are broken as soon as a member is rebound to something else.
    """

    def __init__(self, groups: dict[str, set[str]] | None = None) -> None:
        self._groups: dict[str, set[str]] = groups or {}

    def copy(self) -> _Aliases:
        copied: dict[str, set[str]] = {}
        for group in self._groups.values():
            shared = set(group)
            for name in shared:
                copied[name] = shared
        return _Aliases(copied)

    def group(self, name: str) -> set[str]:
        return set(self._groups.get(name, {name}))

    def detach(self, name: str) -> None:
        group = self._groups.pop(name, None)
        if group is not None:
            group.discard(name)

    def link(self, name: str, other: str) -> None:
        merged = set(self._groups.get(name, {name}) | self._groups.get(other, {other}))
        for member in merged:
            self._groups[member] = merged


# ---------------------------------------------------------------------------
# The public resolver.


def _guarded_parse(source: str, *, filename: str) -> ast.Module | None:
    """Parse a source, or return ``None`` when parsing cannot complete.

    A deeply nested but perfectly valid expression exhausts the interpreter
    stack inside ``ast`` itself, and an enormous one exhausts memory. Either
    is an abstention, never a crash.
    """

    try:
        return ast.parse(source, filename=filename)
    except (SyntaxError, ValueError, RecursionError, MemoryError, OverflowError):
        return None


def _case_module_names(context: FrozenInspectionContext) -> set[str]:
    """Every module name a document of this case shadows at import time.

    A flat ``numpy.py``, a package ``numpy/__init__.py``, and even a bare
    directory named ``numpy`` (a namespace package) all shadow the installed
    module at run time, so every path component counts, not only the stems.
    """

    names: set[str] = set()
    for document in context.documents:
        parts = Path(document.path).parts
        names.update(parts[:-1])
        if document.path.endswith(".py"):
            stem = Path(document.path).stem
            if stem != "__init__":
                names.add(stem)
    return names


def _is_python_document(document: InspectionDocument) -> bool:
    return document.media_type == "text/x-python" or document.path.endswith(".py")


def resolve_copy_dosage_dataflow(
    context: FrozenInspectionContext,
    *,
    hard_operand: str,
    expectation_operand: str,
    calibration_operand: str,
    parser_id: str,
    parser_version: str,
) -> CopyDosageDataflowResolution:
    operands = {
        _STATE_QUANTIZED: hard_operand,
        _STATE_EXPECTATION: expectation_operand,
        _STATE_CALIBRATION: calibration_operand,
    }
    classifications: list[tuple[InspectionDocument, _Classification]] = []
    unsupported = False
    parse_failure = False
    case_module_names = _case_module_names(context)
    for document in context.documents:
        if not _is_python_document(document):
            continue
        if not _python_parser_supported(document, parser_id, parser_version):
            # A Python document the parser skipped is a document this trace
            # never read. It can hold the estimator, the rounding, or a
            # shadowing module definition, so it abstains exactly as a parse
            # failure does.
            parse_failure = True
            continue
        try:
            source = document.content.decode("utf-8")
        except UnicodeDecodeError:
            parse_failure = True
            continue
        tree = _guarded_parse(source, filename=document.path)
        if tree is None:
            parse_failure = True
            continue
        if _imports_case_module(tree, case_module_names - {Path(document.path).stem}):
            # An import that resolves to another document in this very case
            # shadows the installed module of the same name at run time; what
            # such a module does on import is outside this trace.
            unsupported = True
            continue
        outcome = _document_dose_representations(tree)
        unsupported = unsupported or outcome["unsupported"]
        classifications.extend((document, item) for item in outcome["classifications"])
    states = sorted({item.state for _, item in classifications})
    if len(states) > 1:
        return CopyDosageDataflowResolution("ambiguous", None, None, None, (), None)
    if unsupported or parse_failure:
        # A resolved exposure operand next to an unreadable transform or
        # untraceable control flow could be rebound by it; abstain rather
        # than guess.
        return CopyDosageDataflowResolution("unsupported", None, None, None, (), None)
    if not classifications:
        return CopyDosageDataflowResolution("none", None, None, None, (), None)
    state = states[0]
    spans: list[EvidenceSpan] = []
    for item_document, item in classifications:
        for node in (item.dose_node, item.node):
            if node is not None:
                spans.append(_ast_node_evidence_span(item_document, node))
    operations = sorted({item.operation for _, item in classifications if item.operation})
    return CopyDosageDataflowResolution(
        "unique",
        state,
        operands[state],
        operations[0] if len(operations) == 1 else None,
        tuple(spans),
        classifications[0][0].path,
    )


def _imports_case_module(tree: ast.Module, other_names: set[str]) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] in other_names for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in other_names:
                return True
    return False


def _python_parser_supported(
    document: InspectionDocument, parser_id: str, parser_version: str
) -> bool:
    if document.parser_result_payload is None:
        return False
    value = json.loads(document.parser_result_payload)
    return (
        isinstance(value, dict)
        and value.get("parser_id") == parser_id
        and value.get("parser_version") == parser_version
        and value.get("state") == "parsed"
    )


# ---------------------------------------------------------------------------
# The per-document trace engine.


def _document_dose_representations(tree: ast.Module) -> dict[str, Any]:
    """Trace report-reaching model fits, abstaining instead of raising."""

    try:
        return _document_dose_representations_inner(tree)
    except (RecursionError, MemoryError, OverflowError):
        # A source too deep or too large for the analysis abstains; it never
        # crashes the inspection, and the abstention is this resolver's own.
        return {"classifications": [], "unsupported": True}


def _import_bans(tree: ast.Module) -> bool:
    """Whether any import in the module puts the case outside this trace."""

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] not in _ALLOWED_IMPORT_MODULES for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                # A relative import resolves inside a package this trace
                # cannot see.
                return True
            if (node.module or "").split(".")[0] not in _ALLOWED_IMPORT_MODULES:
                return True
            if any(alias.name == "*" for alias in node.names):
                # A star import binds names this trace never sees.
                return True
    return False


def _document_dose_representations_inner(tree: ast.Module) -> dict[str, Any]:
    """Trace report-reaching model fits across module and function scopes."""

    if _import_bans(tree):
        return {"classifications": [], "unsupported": True}

    functions: dict[str, ast.FunctionDef] = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    called = _called_function_names(tree, functions)
    path_names = _path_like_names(tree)
    ctx = _TraceContext(
        functions=functions,
        aliases_by_path=_import_aliases(tree),
        opaque_callables=frozenset(_rebound_names(tree) & set(functions)),
        path_names=path_names,
        reaching=_report_reaching_names(tree, functions, path_names, called),
    )
    classifications: list[_Classification] = []

    module_env: dict[str, _Value] = {}
    module_aliases = _Aliases()
    _scan_scope(
        [item for item in tree.body if not isinstance(item, ast.FunctionDef)],
        module_env,
        module_aliases,
        ctx,
        classifications,
        returns_reach=False,
    )
    for function in functions.values():
        # Function bodies are scanned with parameters masked, so a module
        # global can never stand in for an unbound parameter.
        env: dict[str, _Value] = dict(module_env)
        aliases = module_aliases.copy()
        for parameter in (
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        ):
            aliases.detach(parameter.arg)
            env[parameter.arg] = _OPAQUE
        _scan_scope(
            function.body,
            env,
            aliases,
            ctx,
            classifications,
            returns_reach=function.name in called,
        )

    return {
        "classifications": classifications,
        "unsupported": ctx.unresolved or _has_unsupported_flow(tree),
    }


def _scan_scope(
    statements: list[ast.stmt],
    env: dict[str, _Value],
    aliases: _Aliases,
    ctx: _TraceContext,
    classifications: list[_Classification],
    *,
    returns_reach: bool,
) -> None:
    for statement in _flatten_statements(statements):
        if _statement_reaches(statement, ctx, returns_reach=returns_reach):
            for node in _walk_skipping_lambdas(statement):
                if isinstance(node, ast.Call):
                    value = _tag(node, env, ctx)
                    if isinstance(value, _Fit):
                        _classify_fit(value, node, ctx, classifications)
        _invalidate_mutations(statement, env, aliases)
        _apply_call_effects(statement, env, aliases, ctx)
        _apply_assign(statement, env, aliases, ctx)


def _statement_reaches(statement: ast.stmt, ctx: _TraceContext, *, returns_reach: bool) -> bool:
    if (
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
    ):
        return statement.targets[0].id in ctx.reaching
    if isinstance(statement, ast.Expr) and _write_payloads(statement.value, ctx.path_names):
        return True
    return returns_reach and isinstance(statement, ast.Return)


def _classify_fit(
    fit: _Fit,
    node: ast.AST,
    ctx: _TraceContext,
    classifications: list[_Classification],
) -> None:
    """Classify one report-reaching fit by its uniquely identified exposure operand."""

    regressors = list(fit.regressors)
    model_derived = [item for item in regressors if item.model_derived]
    if model_derived:
        candidates = model_derived
    else:
        # Ruling on genuinely integer input: only a staged column whose
        # integer coding this trace established, feeding the fit unchanged,
        # can stand in for a calibration output.
        candidates = [
            item for item in regressors if item.tag == _QUANTIZED and item.staged and item.unchanged
        ]
    if not candidates:
        return
    if len(candidates) > 1:
        # Two regressors trace to copy-derived values; no structural rule
        # names the exposure, and nomenclature never may.
        ctx.unresolved = True
        return
    dose = candidates[0]
    if dose.tag == _QUANTIZED:
        state = _STATE_QUANTIZED
    elif dose.tag == _CONTINUOUS and dose.origin == _ORIGIN_EXPECTATION:
        state = _STATE_EXPECTATION
    elif dose.tag == _CONTINUOUS and dose.origin == _ORIGIN_CALIBRATION:
        state = _STATE_CALIBRATION
    else:
        ctx.unresolved = True
        return
    classifications.append(
        _Classification(node=node, dose_node=dose.node, state=state, operation=dose.operation)
    )


# ---------------------------------------------------------------------------
# Environment maintenance.


def _bind(name: str, value: _Value, env: dict[str, _Value], aliases: _Aliases) -> None:
    aliases.detach(name)
    env[name] = value


def _invalidate_group(
    name: str, env: dict[str, _Value], aliases: _Aliases, node: ast.AST | None = None
) -> None:
    """Drop the provenance of every name that aliases one mutated object.

    A member that carried provenance becomes an unreadable value rather than a
    plain opaque one, so a later use of it as an exposure operand abstains
    instead of quietly dropping out of the analysis.
    """

    for member in aliases.group(name):
        if _is_traced(env.get(member)) and node is not None:
            env[member] = _unreadable(node)
        else:
            env[member] = _OPAQUE


def _is_traced(value: _Value | None) -> bool:
    """Whether a bound value carries provenance this trace would lose."""

    if isinstance(value, _Col):
        return value.tag != _OPAQUE_TAG
    return isinstance(value, _Rows | _Frame | _Estimator | _Model | _Fit | _Design)


def _tagged(name: str, env: dict[str, _Value], aliases: _Aliases) -> bool:
    return any(_is_traced(env.get(member)) for member in aliases.group(name))


def _statement_touches_tagged(
    statement: ast.stmt, env: dict[str, _Value], aliases: _Aliases
) -> bool:
    return any(
        isinstance(node, ast.Name) and _tagged(node.id, env, aliases)
        for node in ast.walk(statement)
    )


def _target_names(target: ast.expr) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(target):
        if isinstance(node, ast.Name):
            names.add(node.id)
    return names


def _literal_string(node: ast.expr) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _apply_assign(
    statement: ast.stmt, env: dict[str, _Value], aliases: _Aliases, ctx: _TraceContext
) -> None:
    """Update the environment for one assignment, or abstain for the document.

    A single ``Name`` target and a literal frame-column subscript target are
    modelled exactly. Every other assignment form -- tuple or starred
    targets, chained targets, slice targets, annotated targets, augmented
    assignment, and the walrus operator -- leaves the document unsupported as
    soon as it touches a name whose provenance is tagged, because the
    environment cannot follow it.
    """

    if not isinstance(statement, ast.Assign | ast.AugAssign | ast.AnnAssign):
        return
    walrus = any(isinstance(node, ast.NamedExpr) for node in ast.walk(statement))
    if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and not walrus:
        target = statement.targets[0]
        if isinstance(target, ast.Name):
            _apply_name_assign(target, statement.value, env, aliases, ctx)
            return
        if _apply_column_assign(target, statement.value, env, aliases, ctx):
            return
    if _statement_touches_tagged(statement, env, aliases):
        ctx.unresolved = True
    targets: list[ast.expr] = (
        list(statement.targets) if isinstance(statement, ast.Assign) else [statement.target]
    )
    for target in targets:
        for name in _target_names(target):
            _invalidate_group(name, env, aliases, statement)
            _bind(name, _OPAQUE, env, aliases)


def _apply_name_assign(
    target: ast.Name,
    value_node: ast.expr,
    env: dict[str, _Value],
    aliases: _Aliases,
    ctx: _TraceContext,
) -> None:
    if _is_traced_conditional(value_node, env, ctx):
        # A branch decides at run time which value the name holds; no static
        # reading of the guard settles it.
        ctx.unresolved = True
        _bind(target.id, _OPAQUE, env, aliases)
        return
    value = _tag(value_node, env, ctx)
    _bind(target.id, value, env, aliases)
    if isinstance(value_node, ast.Name) and not isinstance(value, _Opaque):
        aliases.link(target.id, value_node.id)
        return
    for name in _container_member_names(value_node):
        if _tagged(name, env, aliases):
            # ``tables = [frame]`` is a second reference to one runtime table.
            # Mutation reached through the container is mutation of the table,
            # so the container name joins the table's invalidation group.
            aliases.link(target.id, name)


def _container_member_names(value_node: ast.expr) -> set[str]:
    """Names a container literal holds a reference to."""

    if not isinstance(value_node, ast.List | ast.Tuple | ast.Set | ast.Dict):
        return set()
    return {node.id for node in ast.walk(value_node) if isinstance(node, ast.Name)}


def _apply_column_assign(
    target: ast.expr,
    value_node: ast.expr,
    env: dict[str, _Value],
    aliases: _Aliases,
    ctx: _TraceContext,
) -> bool:
    """``frame['name'] = expression`` over a traced table, applied in place."""

    if not isinstance(target, ast.Subscript) or not isinstance(target.value, ast.Name):
        return False
    column = _literal_string(target.slice)
    if column is None:
        return False
    current = env.get(target.value.id)
    if not isinstance(current, _Frame):
        return False
    value = _tag(value_node, env, ctx)
    assigned = value if isinstance(value, _Col) else _OPAQUE_COL
    columns = {key: item for key, item in current.columns}
    columns[column] = assigned
    updated = _Frame(tuple(sorted(columns.items())), current.default)
    for member in aliases.group(target.value.id):
        if isinstance(env.get(member), _Frame):
            env[member] = updated
    return True


def _is_traced_conditional(value: ast.expr, env: dict[str, _Value], ctx: _TraceContext) -> bool:
    """A conditional expression choosing between two values this trace follows."""

    if not isinstance(value, ast.IfExp):
        return False
    for branch in (value.body, value.orelse):
        tagged = _tag(branch, env, ctx)
        if isinstance(tagged, _Rows | _Frame | _Estimator | _Design | _Model | _Fit):
            return True
        if isinstance(tagged, _Col) and tagged.tag != _OPAQUE_TAG:
            return True
    return False


def _invalidate_mutations(statement: ast.stmt, env: dict[str, _Value], aliases: _Aliases) -> None:
    """Drop provenance for values a statement mutates or deletes from.

    Every name that aliases the mutated object loses its provenance too: the
    runtime object is one object, and the syntactic receiver is only one of
    its names.
    """

    for node in ast.walk(statement):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            in_place = any(
                keyword.arg == "inplace"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
                for keyword in node.keywords
            )
            if (
                isinstance(node.func.value, ast.Name)
                and (node.func.attr in _MUTATING_METHODS or in_place)
                and node.func.attr not in _AGGREGATE_METHODS
            ):
                _invalidate_group(node.func.value.id, env, aliases, node)
        elif isinstance(node, ast.Delete):
            for item in node.targets:
                inner: ast.expr = item
                while isinstance(inner, ast.Subscript):
                    inner = inner.value
                if isinstance(inner, ast.Name):
                    _invalidate_group(inner.id, env, aliases, node)


# ---------------------------------------------------------------------------
# Call side effects.
#
# Mutation is default-deny. Enumerating the in-place APIs was the demonstrated
# wrong answer: ``numpy.copyto``, an ``out=`` destination, ``.fill``, ``.put``,
# ``.itemset``, ``.resize``, and ``.partition`` each rewrote a traced array
# while the trace went on reporting the value the array used to hold. A call
# whose effect on a traced value this library does not model is therefore
# presumed to write to every traced value its subtree names.


def _apply_call_effects(
    statement: ast.stmt, env: dict[str, _Value], aliases: _Aliases, ctx: _TraceContext
) -> None:
    for node in _walk_skipping_lambdas(statement):
        if isinstance(node, ast.Call):
            _apply_one_call_effect(node, env, aliases, ctx)


def _apply_one_call_effect(
    node: ast.Call, env: dict[str, _Value], aliases: _Aliases, ctx: _TraceContext
) -> None:
    helper = _local_helper(node, env, ctx)
    if helper is not None:
        _helper_effects(helper, node, env, aliases, ctx)
        return
    path = _resolved_call_path(node, ctx)
    if not _recognized_call(node, path):
        _invalidate_named(node, env, aliases, node)
        return
    for keyword in node.keywords:
        if keyword.arg == "out":
            _invalidate_named(keyword.value, env, aliases, node)
    if path in _UFUNC_CALLS and len(node.args) > 1:
        # A ufunc's destination array rides in the position after the operands
        # this trace reads.
        for argument in node.args[1:]:
            _invalidate_named(argument, env, aliases, node)


def _recognized_call(node: ast.Call, path: str | None) -> bool:
    if path is not None and path in _RECOGNIZED_CALL_PATHS:
        return True
    return isinstance(node.func, ast.Attribute) and node.func.attr in _RECOGNIZED_METHODS


def _local_helper(
    node: ast.Call, env: dict[str, _Value], ctx: _TraceContext
) -> ast.FunctionDef | None:
    """The project definition a call runs, when the name resolves to one."""

    if not isinstance(node.func, ast.Name):
        return None
    name = node.func.id
    if name in ctx.opaque_callables or name in env:
        return None
    return ctx.functions.get(name)


def _invalidate_named(
    expression: ast.expr, env: dict[str, _Value], aliases: _Aliases, node: ast.AST
) -> None:
    for inner in ast.walk(expression):
        if isinstance(inner, ast.Name) and _tagged(inner.id, env, aliases):
            _invalidate_group(inner.id, env, aliases, node)


def _helper_effects(
    function: ast.FunctionDef,
    call: ast.Call,
    env: dict[str, _Value],
    aliases: _Aliases,
    ctx: _TraceContext,
) -> None:
    """Write a helper's in-place parameter mutations back to the caller.

    A frame or array handed to a helper is the caller's own object, so a
    column assignment inside the helper is a column assignment on the
    caller's binding. When the body cannot be simulated to completion the
    argument's whole alias group is invalidated instead: an unread body may
    have rewritten it.
    """

    effects = _helper_parameter_effects(function, call, env, ctx)
    if effects is None:
        for argument in (*call.args, *(keyword.value for keyword in call.keywords)):
            _invalidate_named(argument, env, aliases, call)
        return
    for parameter, value in effects.items():
        argument = _argument_for(function, call, parameter)
        if not isinstance(argument, ast.Name):
            continue
        for member in aliases.group(argument.id):
            env[member] = value


def _helper_parameter_effects(
    function: ast.FunctionDef, call: ast.Call, env: dict[str, _Value], ctx: _TraceContext
) -> dict[str, _Value] | None:
    """Each parameter a helper body mutates in place, with its final value.

    A parameter the body rebinds by name is excluded: rebinding a local name
    never reaches the caller's object.
    """

    if ctx.depth >= _MAX_CALL_DEPTH or function.name in ctx.visiting:
        return None
    if not _straight_line_helper(function):
        return None
    callee_env = _bind_call(function, call, env, ctx)
    if callee_env is None:
        return None
    bound = dict(callee_env)
    rebound: set[str] = set()
    ctx.depth += 1
    ctx.visiting.add(function.name)
    try:
        callee_aliases = _Aliases()
        for statement in _flatten_statements(function.body):
            if (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
            ):
                rebound.add(statement.targets[0].id)
            _invalidate_mutations(statement, callee_env, callee_aliases)
            _apply_call_effects(statement, callee_env, callee_aliases, ctx)
            _apply_assign(statement, callee_env, callee_aliases, ctx)
    finally:
        ctx.depth -= 1
        ctx.visiting.discard(function.name)
    return {
        parameter: callee_env[parameter]
        for parameter in bound
        if parameter not in rebound and callee_env.get(parameter) is not bound[parameter]
    }


def _argument_for(function: ast.FunctionDef, call: ast.Call, parameter: str) -> ast.expr | None:
    for index, item in enumerate(function.args.args):
        if item.arg == parameter and index < len(call.args):
            return call.args[index]
    for keyword in call.keywords:
        if keyword.arg == parameter:
            return keyword.value
    return None


# ---------------------------------------------------------------------------
# Expression tagging.


def _tag(node: ast.expr, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
    if ctx.expression_depth >= _MAX_EXPRESSION_DEPTH:
        # Beyond the bound the expression is unread, not benign: a value built
        # by it and used as an exposure operand has to abstain.
        return _unreadable(node)
    ctx.expression_depth += 1
    try:
        return _tag_inner(node, env, ctx)
    finally:
        ctx.expression_depth -= 1


def _tag_inner(node: ast.expr, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
    if isinstance(node, ast.Name):
        return env.get(node.id, _OPAQUE)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return _OPAQUE
        if isinstance(node.value, int) and abs(node.value) > _MAX_LITERAL_MAGNITUDE:
            # Not a quantity this trace reads, and wide enough that converting
            # it raises. Discarding it is an abstention, never a crash.
            return _OPAQUE
        if isinstance(node.value, int | float):
            return _Const(float(node.value))
        return _OPAQUE
    if isinstance(node, ast.List | ast.Tuple):
        if not node.elts:
            return _EMPTY_LIST
        literals = _literal_sequence(node)
        return _Literals(literals) if literals is not None else _OPAQUE
    if isinstance(node, ast.Call):
        return _tag_call(node, env, ctx)
    if isinstance(node, ast.Attribute):
        return _tag_attribute(node, env, ctx)
    if isinstance(node, ast.Subscript):
        return _tag_subscript(node, env, ctx)
    if isinstance(node, ast.BinOp):
        return _tag_binop(node, env, ctx)
    if isinstance(node, ast.UnaryOp):
        inner = _tag(node.operand, env, ctx)
        if isinstance(node.op, ast.USub | ast.UAdd):
            if isinstance(inner, _Const):
                return _Const(-inner.value if isinstance(node.op, ast.USub) else inner.value)
            if isinstance(inner, _Col):
                return inner
        return _OPAQUE
    if isinstance(node, ast.Compare):
        return _tag_compare(node, env, ctx)
    if isinstance(node, ast.ListComp | ast.GeneratorExp):
        return _tag_comprehension(node, env, ctx)
    return _OPAQUE


def _literal_constant(node: ast.expr) -> float | None:
    """A numeric literal, or its negation, and nothing else.

    No arithmetic is folded and no call is evaluated. ``3 / 2`` is not the
    literal ``1.5`` here and ``int(1.5)`` is not the literal ``1``: a branch
    value, a level value, or a decimal count that is not written as a literal
    is unread, and an unread value on the exposure path abstains.
    """

    inner: ast.expr = node
    sign = 1.0
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub | ast.UAdd):
        inner = node.operand
        sign = -1.0 if isinstance(node.op, ast.USub) else 1.0
    if not isinstance(inner, ast.Constant):
        return None
    if isinstance(inner.value, bool) or not isinstance(inner.value, int | float):
        return None
    if isinstance(inner.value, int) and abs(inner.value) > _MAX_LITERAL_MAGNITUDE:
        return None
    return sign * float(inner.value)


def _literal_sequence(node: ast.expr) -> tuple[float, ...] | None:
    if not isinstance(node, ast.List | ast.Tuple):
        return None
    values: list[float] = []
    for item in node.elts:
        value = _literal_constant(item)
        if value is None:
            return None
        values.append(value)
    return tuple(values)


def _as_col(value: _Value) -> _Col | None:
    return value if isinstance(value, _Col) else None


def _tag_attribute(node: ast.Attribute, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
    inner = _tag(node.value, env, ctx)
    if node.attr in _SHAPE_ATTRIBUTES and isinstance(inner, _Col | _Frame | _Design):
        return inner
    return _abstain_or_opaque(node, inner)


def _tag_subscript(node: ast.Subscript, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
    receiver = _tag(node.value, env, ctx)
    column = _literal_string(node.slice)
    if isinstance(receiver, _Rows) and column is not None:
        return _rows_column(receiver, column)
    if isinstance(receiver, _Frame):
        if column is not None:
            return _frame_column(receiver, column)
        columns = _literal_string_sequence(node.slice)
        if columns is not None:
            return _Design(tuple(_frame_column(receiver, item) for item in columns))
        return _OPAQUE
    if isinstance(receiver, _Literals):
        # Indexing a literal table by a traced index. The claim this check
        # implements reads "hard or binned dosage used for a continuous
        # target", so a literal table always bins: three bin centres are
        # three levels whether they are written 0, 1, 2 or 0.12, 0.98, 1.93.
        # A literal table therefore never re-expands a quantized value.
        index_value = _tag(node.slice, env, ctx)
        index = _as_col(index_value)
        if index is None or index.tag in {_OPAQUE_TAG, _TEXT}:
            return _abstain_or_opaque(node, index_value)
        return _Col(
            _QUANTIZED,
            origin=index.origin,
            staged=index.staged,
            unchanged=False,
            node=node,
            operation="literal_table_lookup",
            ids=index.ids,
        )
    if isinstance(receiver, _Col):
        # A positional or boolean row selection preserves the value's scale.
        return replace(receiver, node=receiver.node or node)
    return _OPAQUE


def _literal_string_sequence(node: ast.expr) -> tuple[str, ...] | None:
    if not isinstance(node, ast.List | ast.Tuple):
        return None
    values: list[str] = []
    for item in node.elts:
        text = _literal_string(item)
        if text is None:
            return None
        values.append(text)
    return tuple(values)


def _rows_column(rows: _Rows, column: str) -> _Value:
    for key, value in rows.columns:
        if key == column:
            return value
    return rows.default if rows.default is not None else _OPAQUE


def _frame_column(frame: _Frame, column: str) -> _Col:
    for key, value in frame.columns:
        if key == column:
            return value
    return frame.default if frame.default is not None else _OPAQUE_COL


def _tag_compare(node: ast.Compare, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
    """A comparison yields a two-valued mask, which is a quantized value."""

    values = [_tag(item, env, ctx) for item in (node.left, *node.comparators)]
    operands = [_as_col(item) for item in values]
    traced = [item for item in operands if item is not None]
    if not traced or any(item.tag == _OPAQUE_TAG for item in traced):
        return _abstain_or_opaque(node, *values)
    origin = next((item.origin for item in traced if item.origin is not None), None)
    return _Col(
        _QUANTIZED,
        origin=origin,
        staged=any(item.staged for item in traced),
        unchanged=False,
        node=node,
        operation="threshold_comparison",
        ids=_joined_ids(*values),
    )


def _tag_binop(node: ast.BinOp, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
    left = _tag(node.left, env, ctx)
    right = _tag(node.right, env, ctx)
    if isinstance(node.op, ast.MatMult):
        product = _expectation_product(left, right, node)
        if product is not None:
            return product
        if any(isinstance(item, _Literals) and item.ordered_states for item in (left, right)):
            # An ordered copy-state vector is being weighted by something this
            # library never established as class probabilities.
            return _unreadable(node, left, right)
        return _abstain_or_opaque(node, left, right)
    if isinstance(node.op, ast.Mult):
        expectation = _expectation_terms(left, right, node)
        if expectation is not None:
            return expectation
    if isinstance(node.op, ast.FloorDiv):
        base = _as_col(left)
        if base is None or base.tag in {_OPAQUE_TAG, _TEXT}:
            return _abstain_or_opaque(node, left, right)
        return _quantize(base, node, "floor_division")
    if not isinstance(node.op, ast.Add | ast.Sub | ast.Mult | ast.Div | ast.Pow | ast.Mod):
        return _abstain_or_opaque(node, left, right)
    return _combine(left, right, node)


def _combine(left: _Value, right: _Value, node: ast.AST) -> _Value:
    """Arithmetic over two traced values.

    An *independently* traced continuous operand restores the continuous
    scale; a literal constant does not, so scaling or shifting a quantized
    value keeps it quantized.

    Independence is the whole rule. ``x - x % 1`` is ``floor(x)`` and
    ``x + (round(x) - x)`` is ``round(x)``: in each, the second operand
    descends from the first, and reading the pair by tag alone reports a
    rounded exposure as continuous. So arithmetic over two traced values
    whose provenance sets intersect is unreadable, whatever their tags. A
    dependent continuous operand can cancel exactly the fraction its partner
    carries, and no static reading of the pair settles which happened.
    """

    operands = [item for item in (left, right) if isinstance(item, _Col)]
    others = [item for item in (left, right) if not isinstance(item, _Col)]
    if not operands or any(not isinstance(item, _Const | _Literals) for item in others):
        return _abstain_or_opaque(node, left, right)
    if any(item.tag in {_OPAQUE_TAG, _TEXT} for item in operands):
        return _abstain_or_opaque(node, left, right)
    if len(operands) == 2 and operands[0].ids & operands[1].ids:
        return _unreadable(node, *operands)
    tag = _CONTINUOUS if any(item.tag == _CONTINUOUS for item in operands) else _QUANTIZED
    origin = next((item.origin for item in operands if item.origin is not None), None)
    if origin == _ORIGIN_EXPECTATION_TERMS:
        origin = None
    return _Col(
        tag,
        origin=origin,
        staged=any(item.staged for item in operands),
        unchanged=False,
        node=node,
        operation=None,
        ids=_joined_ids(*operands),
    )


def _expectation_terms(left: _Value, right: _Value, node: ast.AST) -> _Col | None:
    """``probabilities * [0, 1, 2]`` before its row-wise sum."""

    for probabilities, states in ((left, right), (right, left)):
        column = _as_col(probabilities)
        if (
            column is not None
            and column.origin == _ORIGIN_PROBABILITIES
            and isinstance(states, _Literals)
            and states.ordered_states
        ):
            return _Col(
                _CONTINUOUS,
                origin=_ORIGIN_EXPECTATION_TERMS,
                staged=column.staged,
                unchanged=False,
                node=node,
                operation="class_probability_weighting",
                ids=column.ids,
            )
    return None


def _expectation_product(left: _Value, right: _Value, node: ast.AST) -> _Col | None:
    """``probabilities @ [0, 1, 2]``: the posterior expected copy count."""

    for probabilities, states in ((left, right), (right, left)):
        column = _as_col(probabilities)
        if (
            column is not None
            and column.origin == _ORIGIN_PROBABILITIES
            and isinstance(states, _Literals)
            and states.ordered_states
        ):
            return _Col(
                _CONTINUOUS,
                origin=_ORIGIN_EXPECTATION,
                staged=column.staged,
                unchanged=False,
                node=node,
                operation="posterior_expectation_product",
                ids=column.ids,
            )
    return None


def _unreadable(node: ast.AST, *sources: _Value) -> _Col:
    """A dose-shaped step this library cannot read, carrying its provenance."""

    columns = [item for item in sources if isinstance(item, _Col)]
    return _Col(
        _OPAQUE_TAG,
        origin=_ORIGIN_UNREADABLE,
        staged=any(item.staged for item in columns),
        unchanged=False,
        node=node,
        operation="unreadable_step",
        ids=_joined_ids(*sources),
    )


def _carries_model_origin(*values: _Value) -> bool:
    return any(isinstance(item, _Col) and item.model_derived for item in values)


def _abstain_or_opaque(node: ast.AST, *sources: _Value) -> _Value:
    """Abstain when an unreadable step sits on a copy-model value's path."""

    if _carries_model_origin(*sources):
        return _unreadable(node, *sources)
    return _OPAQUE


def _quantize(base: _Col, node: ast.AST, operation: str) -> _Col:
    return _Col(
        _QUANTIZED,
        origin=base.origin,
        staged=base.staged,
        unchanged=False,
        node=node,
        operation=operation,
        ids=base.ids,
    )


def _tag_comprehension(
    node: ast.ListComp | ast.GeneratorExp, env: dict[str, _Value], ctx: _TraceContext
) -> _Value:
    if len(node.generators) != 1:
        return _OPAQUE
    generator = node.generators[0]
    if not isinstance(generator.target, ast.Name) or generator.ifs:
        return _OPAQUE
    source = _tag(generator.iter, env, ctx)
    if not isinstance(source, _Rows):
        return _OPAQUE
    local = dict(env)
    local[generator.target.id] = source
    if isinstance(node.elt, ast.Dict):
        return _row_element_rows(node.elt, generator.target.id, source, local, ctx)
    element = _tag(node.elt, local, ctx)
    if isinstance(element, _Rows | _Col):
        return element
    if isinstance(element, _Const):
        # One literal value per row is a level set of size one, and a literal
        # level set is a binning whatever its values are.
        return _Col(_QUANTIZED, node=node, ids=_fresh_ids())
    return _OPAQUE


def _row_element_rows(
    element: ast.Dict,
    loop_var: str,
    source: _Rows,
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Value:
    """The row set a per-row dictionary literal builds.

    Dictionary construction is order-sensitive: ``{'copy': ..., **row}`` keeps
    the spread's value for ``copy`` and ``{**row, 'copy': ...}`` keeps the
    explicit one. Entries are therefore applied strictly left to right, and a
    later spread overwrites an earlier explicit key with whatever that spread
    carries -- opaque when the spread's own contents do not say.
    """

    built: dict[str, _Col] = {}
    default: _Col | None = None
    for key, value in zip(element.keys, element.values, strict=True):
        if key is None:
            if not (isinstance(value, ast.Name) and value.id == loop_var):
                return _OPAQUE
            for existing in list(built):
                carried = _rows_column(source, existing)
                built[existing] = carried if isinstance(carried, _Col) else _OPAQUE_COL
            for name, carried_column in source.columns:
                built[name] = carried_column
            default = source.default
            continue
        name = _literal_string(key)
        if name is None:
            return _OPAQUE
        tagged = _tag(value, env, ctx)
        built[name] = tagged if isinstance(tagged, _Col) else _OPAQUE_COL
    return _Rows(tuple(sorted(built.items())), default)


# ---------------------------------------------------------------------------
# Call tagging.


def _tag_call(node: ast.Call, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
    value = _tag_call_inner(node, env, ctx)
    if isinstance(value, _Opaque) and _dose_shaped(node, env):
        # An unrecognized call applied to a copy-model value is a step on the
        # exposure path this library cannot read.
        return _unreadable(node)
    return value


def _dose_shaped(node: ast.AST, env: dict[str, _Value]) -> bool:
    """Whether an expression mentions a value this trace ties to copy modelling.

    The scan is syntactic and shallow on purpose: re-tagging every argument of
    every unrecognized call would be exponential in nesting depth.
    """

    for item in ast.walk(node):
        if isinstance(item, ast.Name):
            bound = env.get(item.id)
            if isinstance(bound, _Col) and bound.model_derived:
                return True
            if isinstance(bound, _Estimator):
                return True
            if isinstance(bound, _Fit) and bound.estimator is not None:
                return True
        if isinstance(item, ast.Attribute) and item.attr in _PREDICTION_METHODS:
            return True
    return False


def _tag_call_inner(node: ast.Call, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
    if isinstance(node.func, ast.Attribute):
        return _tag_method_call(node, env, ctx)
    name = node.func.id if isinstance(node.func, ast.Name) else None
    if name is None:
        return _OPAQUE
    if name in ctx.opaque_callables:
        # The name is rebound somewhere in the module, so which body runs here
        # is a runtime question.
        return _OPAQUE
    if name in env:
        # The callable name is bound to a value this trace is following, so
        # the library vocabulary below does not describe it.
        return _OPAQUE
    if name in ctx.functions:
        # A project definition shadows the library vocabulary; its body, not
        # its name, says what it returns.
        return _bound_return_value(ctx.functions[name], node, env, ctx)
    return _tag_library_call(node, _resolved_call_path(node, ctx), env, ctx)


def _tag_method_call(node: ast.Call, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
    assert isinstance(node.func, ast.Attribute)
    path = _resolved_call_path(node, ctx)
    if path is not None:
        library = _tag_library_call(node, path, env, ctx)
        if not isinstance(library, _Opaque):
            return library
    receiver = _tag(node.func.value, env, ctx)
    return _tag_receiver_method(node, node.func.attr, receiver, env, ctx)


def _tag_receiver_method(
    node: ast.Call,
    attribute: str,
    receiver: _Value,
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Value:
    if isinstance(receiver, _Estimator):
        return _tag_estimator_method(node, attribute, receiver, env, ctx)
    if isinstance(receiver, _Fit) and receiver.estimator is not None:
        # ``estimator.fit(X, y)`` returns the estimator itself, so predictions
        # made from the returned handle keep the constructor's category.
        return _tag_estimator_method(node, attribute, receiver.estimator, env, ctx)
    if isinstance(receiver, _Model) and attribute == "fit":
        return _Fit(receiver.regressors)
    if isinstance(receiver, _Frame | _Rows) and attribute in {"copy"}:
        return receiver
    if isinstance(receiver, _Col):
        return _tag_column_method(node, attribute, receiver, env, ctx)
    if attribute in _PREDICTION_METHODS:
        # A prediction from an estimator whose construction this trace never
        # saw is a dose-shaped step it cannot read.
        return _unreadable(node, receiver)
    return _abstain_or_opaque(node, receiver)


def _tag_estimator_method(
    node: ast.Call,
    attribute: str,
    estimator: _Estimator,
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Value:
    if attribute == "fit":
        design = _design_argument(node, env, ctx, position=0, keyword="X")
        return _Fit(design.regressors if design is not None else (), estimator)
    if attribute == "predict_proba":
        if estimator.category != "classifier":
            return _unreadable(node)
        return _Col(
            _CONTINUOUS,
            origin=_ORIGIN_PROBABILITIES,
            node=node,
            operation="class_probability_prediction",
            ids=_fresh_ids(),
        )
    if attribute == "predict":
        if estimator.category == "classifier":
            return _Col(
                _QUANTIZED,
                origin=_ORIGIN_HARD_CALL,
                node=node,
                operation="classifier_hard_call_prediction",
                ids=_fresh_ids(),
            )
        return _Col(
            _CONTINUOUS,
            origin=_ORIGIN_CALIBRATION,
            node=node,
            operation="continuous_calibration_prediction",
            ids=_fresh_ids(),
        )
    return _OPAQUE


def _tag_column_method(
    node: ast.Call,
    attribute: str,
    column: _Col,
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Value:
    if attribute == "astype":
        return _cast(column, _dtype_argument(node), node)
    if attribute in _ROUNDING_METHODS:
        if attribute == "round":
            gate = _rounding_gate(node, digits_position=0)
            if gate == _ROUND_PRESERVING:
                return column
            if gate == _ROUND_UNREADABLE:
                return _unreadable(node, column)
        return _quantize(column, node, f"{attribute}_to_integers")
    if attribute in _BINNING_METHODS:
        return _quantize(column, node, f"{attribute}_index")
    if attribute in _AGGREGATE_METHODS:
        if column.origin == _ORIGIN_EXPECTATION_TERMS:
            return _Col(
                _CONTINUOUS,
                origin=_ORIGIN_EXPECTATION,
                staged=column.staged,
                node=node,
                operation="posterior_expectation_sum",
                ids=column.ids,
            )
        return replace(column, origin=None, unchanged=False, node=node)
    if attribute in _SHAPE_METHODS:
        if attribute == "to_numpy" and (node.args or _has_dtype_keyword(node)):
            # ``to_numpy(dtype=int)`` truncates exactly as ``astype(int)``
            # does; the conversion is spelled as a keyword, not as a cast.
            return _cast(column, _dtype_argument(node), node)
        return column
    if attribute == "clip":
        return replace(column, unchanged=False, node=column.node or node)
    if attribute == "map":
        return _mapped(column, node, env, ctx)
    if attribute == "dot":
        if node.args:
            product = _expectation_product(column, _tag(node.args[0], env, ctx), node)
            if product is not None:
                return product
        return _abstain_or_opaque(node, column)
    return _abstain_or_opaque(node, column)


def _mapped(column: _Col, node: ast.Call, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
    """``series.map({0: 0.12, 1: 0.98, 2: 1.93})`` over a dict literal.

    A literal dictionary is a lookup table, so it bins whatever its values
    are. Three named levels are three levels even when they are written as
    decimals.
    """

    if len(node.args) != 1 or node.keywords:
        return _unreadable(node, column)
    mapping = node.args[0]
    if not isinstance(mapping, ast.Dict):
        # A dictionary assembled at run time cannot be read statically.
        return _unreadable(node, column)
    values: list[float] = []
    for key, value in zip(mapping.keys, mapping.values, strict=True):
        if key is None:
            return _unreadable(node, column)
        literal = _literal_constant(value)
        if literal is None:
            return _unreadable(node, column)
        values.append(literal)
    if not values:
        return _unreadable(node, column)
    return _Col(
        _QUANTIZED,
        origin=column.origin,
        staged=column.staged,
        unchanged=False,
        node=node,
        operation="literal_dictionary_map",
        ids=column.ids,
    )


_ROUND_TO_LEVELS = "levels"
_ROUND_PRESERVING = "preserving"
_ROUND_UNREADABLE = "unreadable"


def _rounding_gate(node: ast.Call, *, digits_position: int) -> str:
    """How a rounding call's stated decimal count changes the scale.

    ``round(x)``, ``round(x, 0)``, and ``round(x, -1)`` all land the value on
    a finite set of levels: rounding to tens bins as surely as rounding to
    units, and reading a negative count as scale-preserving was a
    demonstrated wrong answer. ``round(x, 2)`` preserves the scale. A count
    written as anything but a literal is unreadable, because it may be zero.
    """

    digits = node.args[digits_position] if len(node.args) > digits_position else None
    for keyword in node.keywords:
        if keyword.arg in {"decimals", "ndigits"}:
            digits = keyword.value
    if digits is None:
        return _ROUND_TO_LEVELS
    value = _literal_constant(digits)
    if value is None or not float(value).is_integer():
        return _ROUND_UNREADABLE
    return _ROUND_TO_LEVELS if value <= 0 else _ROUND_PRESERVING


def _has_dtype_keyword(node: ast.Call) -> bool:
    return any(keyword.arg == "dtype" for keyword in node.keywords)


def _dtype_argument(node: ast.Call, *, position: int = 0) -> str | None:
    candidate: ast.expr | None = node.args[position] if len(node.args) > position else None
    for keyword in node.keywords:
        if keyword.arg == "dtype":
            candidate = keyword.value
    if candidate is None:
        return None
    text = _literal_string(candidate)
    if text is not None:
        return text
    if isinstance(candidate, ast.Name):
        return candidate.id
    if isinstance(candidate, ast.Attribute):
        return candidate.attr
    return None


def _cast(column: _Col, dtype: str | None, node: ast.AST) -> _Value:
    if dtype is None or dtype not in _INTEGER_DTYPES | _FLOAT_DTYPES:
        # A dtype this trace cannot read may be an integer dtype, and an
        # integer dtype truncates. That is a step on the exposure path this
        # library cannot read.
        if column.tag == _OPAQUE_TAG:
            return _OPAQUE
        return _unreadable(node, column)
    if dtype in _INTEGER_DTYPES:
        if column.tag == _TEXT:
            # Parsing an integer out of staged text establishes integer
            # coding; it does not quantize a continuous value.
            return _Col(
                _QUANTIZED,
                origin=column.origin,
                staged=column.staged,
                unchanged=column.unchanged,
                node=node,
                operation="staged_integer_parse",
            )
        if column.tag == _OPAQUE_TAG:
            return _OPAQUE
        return _quantize(column, node, "integer_cast")
    if dtype in _FLOAT_DTYPES:
        if column.tag == _TEXT:
            return _Col(
                _CONTINUOUS,
                origin=column.origin,
                staged=column.staged,
                unchanged=column.unchanged,
                node=node,
                operation="staged_float_parse",
            )
        if column.tag == _OPAQUE_TAG:
            return _OPAQUE
        # A float cast never restores information a quantizer removed.
        return replace(column, unchanged=False, node=column.node or node)
    return _OPAQUE


def _tag_library_call(
    node: ast.Call, path: str | None, env: dict[str, _Value], ctx: _TraceContext
) -> _Value:
    if path is None:
        return _OPAQUE
    if path in _STAGED_FRAME_CALLS:
        return _Frame(
            default=_Col(_OPAQUE_TAG, staged=True, unchanged=True, node=node, ids=_fresh_ids())
        )
    if path in _STAGED_ROW_CALLS:
        return _Rows(default=_Col(_TEXT, staged=True, unchanged=True, node=node, ids=_fresh_ids()))
    if path in _CLASSIFIER_CONSTRUCTORS:
        return _Estimator("classifier")
    if path in _CONTINUOUS_CONSTRUCTORS:
        return _Estimator("continuous")
    if path in _OPAQUE_ESTIMATOR_CONSTRUCTORS:
        return _OPAQUE
    if path in _MODEL_CONSTRUCTORS:
        design = _design_argument(
            node, env, ctx, position=_MODEL_CONSTRUCTORS[path], keyword="exog"
        )
        return _Model(design.regressors) if design is not None else _Model(())
    if path in _CONSTANT_CALLS:
        design = _design_argument(node, env, ctx, position=0, keyword="data")
        return _Design(design.regressors) if design is not None else _OPAQUE
    if path in _DESIGN_CALLS:
        return _stacked_design(node, env, ctx)
    if path == "pandas.DataFrame":
        return _frame_literal(node, env, ctx)
    if path in {"numpy.array", "numpy.asarray", "numpy.asfarray"}:
        if not node.args:
            return _OPAQUE
        built = _tag(node.args[0], env, ctx)
        if len(node.args) < 2 and not _has_dtype_keyword(node):
            return built
        # ``numpy.array(x, dtype=int)`` truncates exactly as ``astype(int)``
        # does. The constructor's dtype argument is a cast written in another
        # position, not a re-wrapping of the same values.
        base = _as_col(built)
        if base is None:
            return _abstain_or_opaque(node, built)
        return _cast(base, _dtype_argument(node, position=1), node)
    if path in _PRESERVING_CALLS:
        base = _as_col(_tag(node.args[0], env, ctx)) if node.args else None
        if base is None:
            return _OPAQUE
        return replace(base, unchanged=False, node=base.node or node)
    if path in _ROUNDING_CALLS:
        base = _as_col(_tag(node.args[0], env, ctx)) if node.args else None
        if base is None or base.tag in {_OPAQUE_TAG, _TEXT}:
            return _OPAQUE
        if path in {"numpy.round", "numpy.around"}:
            gate = _rounding_gate(node, digits_position=1)
            if gate == _ROUND_PRESERVING:
                return base
            if gate == _ROUND_UNREADABLE:
                return _unreadable(node, base)
        return _quantize(base, node, "rounding_to_integers")
    if path in _BINNING_CALLS:
        index = 1 if path == "numpy.searchsorted" else 0
        base = _as_col(_tag(node.args[index], env, ctx)) if len(node.args) > index else None
        if base is None or base.tag in {_OPAQUE_TAG, _TEXT}:
            return _OPAQUE
        return _quantize(base, node, "binning_index")
    if path in _TABLE_CALLS:
        return _binned_labels(node, env, ctx)
    if path == "numpy.where":
        return _tag_where(node, env, ctx)
    if path in {"numpy.sum", "numpy.nansum", "numpy.mean"}:
        base = _as_col(_tag(node.args[0], env, ctx)) if node.args else None
        if base is None:
            return _OPAQUE
        if base.origin == _ORIGIN_EXPECTATION_TERMS:
            return _Col(
                _CONTINUOUS,
                origin=_ORIGIN_EXPECTATION,
                staged=base.staged,
                node=node,
                operation="posterior_expectation_sum",
                ids=base.ids,
            )
        return replace(base, origin=None, unchanged=False, node=node)
    if path in {"numpy.dot", "numpy.matmul", "numpy.inner"}:
        if len(node.args) != 2:
            return _OPAQUE
        product = _expectation_product(
            _tag(node.args[0], env, ctx), _tag(node.args[1], env, ctx), node
        )
        return product or _OPAQUE
    if path in {"builtins.int", "builtins.float"}:
        if len(node.args) != 1 or node.keywords:
            return _OPAQUE
        inner = _tag(node.args[0], env, ctx)
        if isinstance(inner, _Const):
            # ``int(1.5)`` folds to nothing: the call truncates, so its result
            # is not the literal that was written. Only a call that leaves the
            # literal alone reads as that literal.
            if path == "builtins.int" and not float(inner.value).is_integer():
                return _OPAQUE
            return inner
        base = _as_col(inner)
        if base is None:
            return _OPAQUE
        return _cast(base, "int" if path.endswith("int") else "float", node)
    if path == "builtins.round":
        base = _as_col(_tag(node.args[0], env, ctx)) if node.args else None
        if base is None or base.tag in {_OPAQUE_TAG, _TEXT}:
            return _OPAQUE
        gate = _rounding_gate(node, digits_position=1)
        if gate == _ROUND_PRESERVING:
            return base
        if gate == _ROUND_UNREADABLE:
            return _unreadable(node, base)
        return _quantize(base, node, "rounding_to_integers")
    if path == "builtins.list":
        if len(node.args) != 1 or node.keywords:
            return _OPAQUE
        inner = _tag(node.args[0], env, ctx)
        return inner if isinstance(inner, _Rows | _Col | _Literals) else _OPAQUE
    if path in {"builtins.len", "builtins.sum", "builtins.abs", "builtins.max", "builtins.min"}:
        return _OPAQUE
    return _OPAQUE


def _tag_where(node: ast.Call, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
    """``numpy.where(condition, a, b)``.

    Two literal branches are two levels, so the result is quantized whatever
    the two literals are: ``where(c, 0.12, 1.93)`` assigns a value from a
    two-entry table exactly as ``where(c, 0, 1)`` does. A branch that is
    neither a literal nor a traced value is unread, and an unread branch on
    the exposure path abstains rather than falling through.
    """

    if len(node.args) != 3:
        return _OPAQUE
    condition = _as_col(_tag(node.args[0], env, ctx))
    literals = [_literal_constant(item) for item in node.args[1:]]
    if all(item is not None for item in literals):
        return _Col(
            _QUANTIZED,
            origin=condition.origin if condition is not None else None,
            staged=condition.staged if condition is not None else False,
            unchanged=False,
            node=node,
            operation="literal_branch_selection",
            ids=condition.ids if condition is not None else frozenset(),
        )
    branches = [
        _tag(item, env, ctx) if literal is None else _Const(literal)
        for item, literal in zip(node.args[1:], literals, strict=True)
    ]
    columns = [item for item in branches if isinstance(item, _Col)]
    if len(columns) != len([item for item in branches if not isinstance(item, _Const)]):
        return _abstain_or_opaque(node, condition or _OPAQUE, *branches)
    if any(item.tag in {_OPAQUE_TAG, _TEXT} for item in columns):
        return _abstain_or_opaque(node, condition or _OPAQUE, *branches)
    tag = _CONTINUOUS if any(item.tag == _CONTINUOUS for item in columns) else _QUANTIZED
    return _Col(
        tag,
        origin=next((item.origin for item in columns if item.origin is not None), None),
        staged=any(item.staged for item in columns),
        unchanged=False,
        node=node,
        operation="branch_selection",
        ids=_joined_ids(*columns),
    )


def _binned_labels(node: ast.Call, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
    """``pandas.cut(values, bins, labels=[...])`` over a literal label sequence."""

    base = _as_col(_tag(node.args[0], env, ctx)) if node.args else None
    if base is None or base.tag in {_OPAQUE_TAG, _TEXT}:
        return _OPAQUE
    labels = None
    for keyword in node.keywords:
        if keyword.arg == "labels":
            labels = _literal_sequence(keyword.value)
    if labels is None:
        return _OPAQUE
    # A cut assigns one label per bin. The labels are the levels, so the
    # result bins whether they are written 0, 1, 2 or 0.12, 0.98, 1.93.
    return _Col(
        _QUANTIZED,
        origin=base.origin,
        staged=base.staged,
        unchanged=False,
        node=node,
        operation="binned_label_assignment",
        ids=base.ids,
    )


# ---------------------------------------------------------------------------
# Design matrices and fits.


def _design_argument(
    node: ast.Call,
    env: dict[str, _Value],
    ctx: _TraceContext,
    *,
    position: int,
    keyword: str,
) -> _Design | None:
    candidate: ast.expr | None = node.args[position] if len(node.args) > position else None
    for item in node.keywords:
        if item.arg == keyword:
            candidate = item.value
    if candidate is None:
        return None
    return _as_design(_tag(candidate, env, ctx))


def _as_design(value: _Value) -> _Design:
    if isinstance(value, _Design):
        return value
    if isinstance(value, _Col):
        return _Design((value,))
    if isinstance(value, _Frame):
        return _Design(tuple(item for _, item in value.columns))
    if isinstance(value, _Model | _Fit):
        return _Design(value.regressors)
    return _Design((_OPAQUE_COL,))


def _stacked_design(node: ast.Call, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
    if len(node.args) != 1:
        return _OPAQUE
    argument = node.args[0]
    if not isinstance(argument, ast.List | ast.Tuple):
        return _OPAQUE
    regressors: list[_Col] = []
    for item in argument.elts:
        value = _tag(item, env, ctx)
        if isinstance(value, _Design):
            regressors.extend(value.regressors)
        elif isinstance(value, _Col):
            regressors.append(value)
        elif isinstance(value, _Const):
            continue
        else:
            regressors.append(_OPAQUE_COL)
    return _Design(tuple(regressors))


def _frame_literal(node: ast.Call, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
    if len(node.args) != 1 or not isinstance(node.args[0], ast.Dict):
        return _OPAQUE
    mapping = node.args[0]
    columns: dict[str, _Col] = {}
    for key, value in zip(mapping.keys, mapping.values, strict=True):
        name = _literal_string(key) if key is not None else None
        if name is None:
            return _OPAQUE
        tagged = _tag(value, env, ctx)
        columns[name] = tagged if isinstance(tagged, _Col) else _OPAQUE_COL
    return _Frame(tuple(sorted(columns.items())))


# ---------------------------------------------------------------------------
# Helper-function tracing.


def _bind_call(
    function: ast.FunctionDef,
    call: ast.Call,
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> dict[str, _Value] | None:
    if (
        function.args.posonlyargs
        or function.args.kwonlyargs
        or function.args.vararg
        or function.args.kwarg
    ):
        return None
    parameters = [item.arg for item in function.args.args]
    if len(call.args) > len(parameters):
        return None
    bound: dict[str, _Value] = {}
    for parameter, argument in zip(parameters, call.args, strict=False):
        bound[parameter] = _tag(argument, env, ctx)
    for keyword in call.keywords:
        if keyword.arg is None or keyword.arg not in parameters or keyword.arg in bound:
            return None
        bound[keyword.arg] = _tag(keyword.value, env, ctx)
    for parameter in parameters[len(parameters) - len(function.args.defaults) :]:
        bound.setdefault(parameter, _OPAQUE)
    if set(bound) != set(parameters):
        return None
    return bound


def _bound_return_value(
    function: ast.FunctionDef,
    call: ast.Call,
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Value:
    """The return value of a callee with its parameters bound.

    Statements are processed in order and the first top-level return decides;
    a body that continues past its return is not the straight line this
    analysis assumes and reads as opaque.
    """

    if ctx.depth >= _MAX_CALL_DEPTH or function.name in ctx.visiting:
        return _OPAQUE
    if not _straight_line_helper(function):
        return _OPAQUE
    callee_env = _bind_call(function, call, env, ctx)
    if callee_env is None:
        return _OPAQUE
    ctx.depth += 1
    ctx.visiting.add(function.name)
    try:
        callee_aliases = _Aliases()
        statements = _flatten_statements(function.body)
        for index, statement in enumerate(statements):
            if isinstance(statement, ast.Return):
                if statement.value is None or index != len(statements) - 1:
                    return _OPAQUE
                return _tag(statement.value, callee_env, ctx)
            _invalidate_mutations(statement, callee_env, callee_aliases)
            _apply_assign(statement, callee_env, callee_aliases, ctx)
        return _OPAQUE
    finally:
        ctx.depth -= 1
        ctx.visiting.discard(function.name)


def _straight_line_helper(function: ast.FunctionDef) -> bool:
    """A helper body free of walrus bindings and side-effecting statements."""

    for node in ast.walk(function):
        if isinstance(node, ast.NamedExpr):
            return False
    for statement in _flatten_statements(function.body):
        if isinstance(statement, ast.Expr) and not isinstance(statement.value, ast.Constant):
            # A bare expression statement exists for its side effect; only a
            # docstring is inert.
            return False
    return True


# ---------------------------------------------------------------------------
# Import resolution.
#
# An estimator's category comes from the constructor's resolved module path,
# never from the spelling of the variable that holds it. A module alias bound
# by an import statement is a resolution, not nomenclature.


def _import_aliases(tree: ast.Module) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                aliases[item.asname or item.name.split(".")[0]] = (
                    item.name if item.asname else item.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            for item in node.names:
                aliases[item.asname or item.name] = f"{node.module}.{item.name}"
    return aliases


def _dotted_path(node: ast.expr) -> str | None:
    parts: list[str] = []
    current: ast.expr = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    parts.append(current.id)
    return ".".join(reversed(parts))


def _resolved_call_path(node: ast.Call, ctx: _TraceContext) -> str | None:
    dotted = _dotted_path(node.func)
    if dotted is None:
        return None
    head, _, rest = dotted.partition(".")
    if head in ctx.opaque_callables:
        return None
    if head in ctx.aliases_by_path:
        resolved = ctx.aliases_by_path[head]
        return f"{resolved}.{rest}" if rest else resolved
    if not rest and head in _BUILTIN_CALLS:
        return f"builtins.{head}"
    return None


# ---------------------------------------------------------------------------
# Report reachability and control-flow bounds.
#
# Copied from ``founder_orientation_dataflow`` so the two recognizers stay
# independently versionable; see this module's docstring.


def _walk_skipping_lambdas(statement: ast.AST) -> list[ast.AST]:
    found: list[ast.AST] = []
    stack: list[ast.AST] = [statement]
    while stack:
        node = stack.pop()
        found.append(node)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.Lambda):
                continue
            stack.append(child)
    return found


def _is_path_like(node: ast.expr, path_names: set[str], depth: int = 0) -> bool:
    """Whether an expression resolves to a filesystem path or a handle on one.

    A ``StringIO`` buffer also answers to ``write``, so a diagnostic string
    written into memory would otherwise look exactly like the published
    report. Only a ``Path`` call chain, a name assigned from one, or an
    ``open`` on one counts.
    """

    if depth >= _MAX_EXPRESSION_DEPTH:
        return False
    if isinstance(node, ast.Name):
        return node.id in path_names
    if isinstance(node, ast.Call):
        name = _call_name(node)
        if name in _PATH_CALLS:
            return True
        if name == "open" and node.args:
            return _is_path_like(node.args[0], path_names, depth + 1)
        if isinstance(node.func, ast.Attribute):
            return _is_path_like(node.func.value, path_names, depth + 1)
        return False
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _is_path_like(node.left, path_names, depth + 1) or _is_path_like(
            node.right, path_names, depth + 1
        )
    if isinstance(node, ast.Attribute):
        return _is_path_like(node.value, path_names, depth + 1)
    return False


def _path_like_names(tree: ast.Module) -> frozenset[str]:
    """Names bound, directly or transitively, to a filesystem path."""

    names: set[str] = set()
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            targets: list[ast.expr] = []
            value: ast.expr | None = None
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                targets = [node.targets[0]]
                value = node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                targets = [node.target]
                value = node.value
            elif isinstance(node, ast.withitem) and node.optional_vars is not None:
                targets = [node.optional_vars]
                value = node.context_expr
            if value is None:
                continue
            for target in targets:
                if not isinstance(target, ast.Name) or target.id in names:
                    continue
                if _is_path_like(value, names):
                    names.add(target.id)
                    changed = True
    return frozenset(names)


def _rebound_names(tree: ast.Module) -> set[str]:
    """Every name any binding form in the module can rebind."""

    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                names.update(_target_names(target))
        elif isinstance(node, ast.AugAssign | ast.AnnAssign):
            names.update(_target_names(node.target))
        elif isinstance(node, ast.For | ast.AsyncFor):
            names.update(_target_names(node.target))
        elif isinstance(node, ast.NamedExpr):
            names.update(_target_names(node.target))
        elif isinstance(node, ast.withitem) and node.optional_vars is not None:
            names.update(_target_names(node.optional_vars))
    return names


def _called_function_names(
    tree: ast.Module, functions: dict[str, ast.FunctionDef]
) -> frozenset[str]:
    """Module-level functions some reachable caller actually calls.

    A return statement inside a function nobody calls never delivers a value
    anywhere, so it cannot seed the report-reaching set.
    """

    frontier: set[str] = set()
    for statement in (item for item in tree.body if not isinstance(item, ast.FunctionDef)):
        for node in ast.walk(statement):
            if isinstance(node, ast.Call) and _call_name(node) in functions:
                frontier.add(_call_name(node))
    reached: set[str] = set()
    while frontier:
        name = frontier.pop()
        if name in reached:
            continue
        reached.add(name)
        for node in ast.walk(functions[name]):
            if isinstance(node, ast.Call):
                callee = _call_name(node)
                if callee in functions and callee not in reached:
                    frontier.add(callee)
    return frozenset(reached)


def _write_payloads(node: ast.AST, path_names: frozenset[str] | set[str]) -> list[ast.expr]:
    payloads: list[ast.expr] = []
    for inner in ast.walk(node):
        if (
            isinstance(inner, ast.Call)
            and isinstance(inner.func, ast.Attribute)
            and inner.func.attr in _WRITE_METHODS
            and inner.args
            and _is_path_like(inner.func.value, set(path_names))
        ):
            payloads.append(inner.args[0])
    return payloads


def _report_reaching_names(
    tree: ast.Module,
    functions: dict[str, ast.FunctionDef],
    path_names: frozenset[str],
    called: frozenset[str],
) -> set[str]:
    """Names whose values can flow into a written report payload.

    This is a permit gate only. Widening it can admit a fit that never
    reaches the report, which costs an abstention, and can never change which
    representation a classified fit reports.
    """

    dependencies: dict[str, set[str]] = {}
    seeds: set[str] = set()

    def _depend(target: str, values: list[ast.expr]) -> None:
        free: set[str] = set()
        for value in values:
            free.update(name.id for name in ast.walk(value) if isinstance(name, ast.Name))
        dependencies.setdefault(target, set()).update(free)

    def _collect_edge(node: ast.AST) -> None:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            _depend(node.targets[0].id, [node.value])
            return
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
        ):
            if node.func.attr in {"append", "extend"}:
                _depend(node.func.value.id, list(node.args))
            elif node.func.attr == "insert":
                _depend(node.func.value.id, list(node.args[1:]))
            return
        if (
            isinstance(node, ast.AugAssign)
            and isinstance(node.target, ast.Name)
            and isinstance(node.op, ast.Add | ast.Mult)
        ):
            _depend(node.target.id, [node.value])

    def _collect(statements: list[ast.stmt], *, seed_returns: bool) -> None:
        for statement in _flatten_statements(statements):
            for payload in _write_payloads(statement, path_names):
                for name in ast.walk(payload):
                    if isinstance(name, ast.Name):
                        seeds.add(name.id)
            if seed_returns and isinstance(statement, ast.Return) and statement.value is not None:
                for name in ast.walk(statement.value):
                    if isinstance(name, ast.Name):
                        seeds.add(name.id)
        for statement in statements:
            for node in ast.walk(statement):
                _collect_edge(node)

    _collect(
        [item for item in tree.body if not isinstance(item, ast.FunctionDef)],
        seed_returns=False,
    )
    for function in functions.values():
        _collect(function.body, seed_returns=function.name in called)

    reaching = set(seeds)
    changed = True
    while changed:
        changed = False
        for target, free in dependencies.items():
            if target in reaching and not free <= reaching:
                reaching.update(free)
                changed = True
    return reaching


def _has_unsupported_flow(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.With | ast.AsyncWith):
            continue
        if isinstance(node, ast.If) and _is_main_guard(node):
            continue
        if isinstance(node, _UNSUPPORTED_STATEMENTS):
            if isinstance(node, ast.FunctionDef):
                continue
            return True
    return False


def _is_main_guard(node: ast.If) -> bool:
    test = node.test
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Eq)
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "__main__"
    )


def _flatten_statements(statements: list[ast.stmt]) -> list[ast.stmt]:
    flat: list[ast.stmt] = []
    for statement in statements:
        if isinstance(statement, ast.With):
            flat.extend(_flatten_statements(statement.body))
        elif isinstance(statement, ast.If) and _is_main_guard(statement):
            flat.extend(_flatten_statements(statement.body))
        else:
            flat.append(statement)
    return flat


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
        return f"{node.func.value.id}.{node.func.attr}"
    if isinstance(node.func, ast.Name):
        return node.func.id
    return ""


def _ast_node_evidence_span(document: InspectionDocument, node: ast.AST) -> EvidenceSpan:
    assert document.parser_result_ref is not None
    assert document.source_location is not None
    start_line = getattr(node, "lineno", 1)
    end_line = getattr(node, "end_lineno", start_line)
    lines = document.content.decode("utf-8").splitlines()
    start_column = getattr(node, "col_offset", 0) + 1
    end_offset = getattr(node, "end_col_offset", None)
    if end_offset is None:
        end_column = len(lines[end_line - 1]) if 1 <= end_line <= len(lines) else 1
    else:
        end_column = end_offset + 1
    return EvidenceSpan(
        file_ref=document.file_ref,
        path=document.path,
        content_digest=document.source_location.content_digest,
        start_line=start_line + document.line_offset,
        end_line=end_line + document.line_offset,
        start_column=start_column,
        end_column=end_column,
        parser_result_ref=document.parser_result_ref,
    )
