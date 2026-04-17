.PHONY: install test lint fmt clean

install:
	uv sync --all-extras

test:
	uv run pytest -v

lint:
	uv run ruff check src tests

fmt:
	uv run ruff format src tests

clean:
	rm -rf .pytest_cache .ruff_cache dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
