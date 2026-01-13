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
	@set -e; \
	version=$$(uv version --short); \
	if ! git tag --list | grep -Fxq "$$version"; then \
		git tag "$$version"; \
		git push origin "$$version"; \
	else \
		echo "Tag $$version already exists."; \
	fi
	uv build
	UV_PUBLISH_TOKEN="$(PYPI_TOKEN)" uv publish

changelog:
	git fetch --tags
	HEADER="# Changelog\nAll notable changes to this project will be documented in this file.\n========="; \
	TAG=$$(git describe --tags --abbrev=0); \
	DATE=$$(date +%Y-%m-%d); \
	CHANGES=$$(git log $$TAG..HEAD --pretty=format:"- %s"); \
	NEW_CONTENT="## [$$(uv version --short)] - $$DATE\n\n$$CHANGES\n"; \
	perl -i -0pe "s{$$HEADER}{$$HEADER\n\n$$NEW_CONTENT}s" CHANGELOG.md

new-version:
	uv version --bump patch # minor, major, patch
