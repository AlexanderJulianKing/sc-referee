.PHONY: install test test-parallel lint typecheck validate verify demo clean

install:
	python -m pip install -e '.[dev]'

test:
	pytest

# Opt-in parallel run. Two passes: everything that tolerates competing CPU
# load, then the wall-clock- and order-sensitive tests on their own.
#
# --serial-lane is used instead of -m so the 'not retired_report_lane'
# expression already in addopts is not replaced. --dist loadfile keeps each
# file on one worker, which the module-scoped fixtures and the modules with
# intra-file state dependencies require.
#
# PYTEST_WORKERS defaults to 6, deliberately below the core count so the run
# leaves headroom for other work on the same machine. Raise it for a quiet
# machine, e.g. `make test-parallel PYTEST_WORKERS=auto`; note that returns
# fall off quickly because the wall clock is bounded by the slowest single
# file, not by the worker count.
PYTEST_WORKERS ?= 6

test-parallel:
	pytest -n $(PYTEST_WORKERS) --dist loadfile --serial-lane=exclude
	pytest --serial-lane=only

lint:
	ruff check .
	ruff format --check .

typecheck:
	mypy src

validate:
	python scripts/validate_starter.py

verify:
	python scripts/verify_handoff.py

demo:
	sc-referee demo examples/walking-skeleton --output .demo-audit
	sc-referee replay .demo-audit/semantic.lock.json --output .demo-replay

clean:
	rm -rf .demo-audit .demo-replay .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
