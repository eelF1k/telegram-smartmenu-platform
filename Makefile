PIP ?= pip

.PHONY: install-dev lint test format

install-dev:
	$(PIP) install -e ".[dev]"

lint:
	ruff check .

format:
	ruff format .

test:
	pytest -q
