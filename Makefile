.PHONY: all sync lint format typecheck ci clean determinism

all: lint typecheck

sync:
	uv sync --frozen --all-extras

format:
	uv run ruff format src tests diagnosis/tools

lint:
	uv run ruff check src tests diagnosis/tools
	uv run ruff format --check src tests diagnosis/tools

typecheck:
	uv run mypy src tests

ci: lint typecheck
	@echo "Local static checks passed. Run tests and full determinism on Colab session per project requirements."

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov dist build
