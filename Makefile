.PHONY: sync validate verify-source test lint format-check check

sync:
	uv sync --frozen

validate:
	uv run python scripts/validate_content.py

verify-source:
	@test -n "$(SOURCE)" || (echo "SOURCE is required" && exit 2)
	uv run python -m scripts.verify_migration "$(SOURCE)"

test:
	uv run pytest

lint:
	uv run ruff check .

format-check:
	uv run ruff format --check .

check: validate test lint format-check
