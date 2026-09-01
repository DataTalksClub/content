.PHONY: sync validate validate-repairs validate-editorial-overlay validate-source-correction verify-source attest attest-source-correction test lint format-check check

sync:
	uv sync --frozen

validate:
	uv run python scripts/validate_content.py

validate-repairs:
	uv run python -m scripts.repair_manifest

validate-editorial-overlay:
	uv run python -m scripts.editorial_overlay

validate-source-correction:
	uv run python -m scripts.source_correction

verify-source:
	@test -n "$(SOURCE)" || (echo "SOURCE is required" && exit 2)
	uv run python -m scripts.verify_migration "$(SOURCE)"

attest:
	@test -n "$(COMMIT)" || (echo "COMMIT is required" && exit 2)
	@test -n "$(OUTPUT)" || (echo "OUTPUT is required" && exit 2)
	uv run python -m scripts.repair_manifest \
		--attest-commit "$(COMMIT)" \
		--attestation-output "$(OUTPUT)"

attest-source-correction:
	@test -n "$(COMMIT)" || (echo "COMMIT is required" && exit 2)
	@test -n "$(OUTPUT)" || (echo "OUTPUT is required" && exit 2)
	uv run python -m scripts.source_correction \
		--attest-commit "$(COMMIT)" \
		--attestation-output "$(OUTPUT)"

test:
	uv run pytest

lint:
	uv run ruff check .

format-check:
	uv run ruff format --check .

check: validate validate-repairs validate-editorial-overlay validate-source-correction test lint format-check
