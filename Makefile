.PHONY: install test lint typecheck validate verify demo clean

install:
	python -m pip install -e '.[dev]'

test:
	pytest

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
