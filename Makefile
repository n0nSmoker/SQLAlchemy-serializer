.PHONY: test format test-pypi
FILE = $(file)

test:
	TEST_FILE=$(FILE) docker-compose up --build --abort-on-container-exit

test-benchmark:
	docker-compose run tests uv run pytest --benchmark-only

test-pypi:
	uv run pytest -xvrs --color=yes -m pypi tests/test_pypi_readiness.py

format:
	uv run ruff format .
	uv run ruff check --fix .

publish:
	uv build --no-sources
	UV_PUBLISH_TOKEN="$(PYPI_TOKEN)" uv publish

changelog:
	git fetch --tags
	HEADER="# Changelog\nAll notable changes to this project will be documented in this file.\n========="; \
	TAG=$$(git describe --tags --abbrev=0); \
	DATE=$$(date +%Y-%m-%d); \
	CHANGES=$$(git log $$TAG..HEAD --pretty=format:"- %s"); \
	NEW_CONTENT="$$HEADER\n\n## [$$(uv version --short)] - $$DATE\n\n$$CHANGES\n"; \
	perl -i -0pe "s{$$HEADER}{$$NEW_CONTENT}s" CHANGELOG.md

new-version:
	uv version --bump minor # minor, major, patch