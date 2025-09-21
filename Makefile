format:
	uv run black src/

lint_mypy:
	uv run mypy src/

lint_pylint:
	uv run pylint src/

lint: lint_mypy lint_pylint

.PHONY: format lint_mypy lint_pylint lint
