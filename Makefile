.PHONY: test format test-pypi
FILE = $(file)

test:
	TEST_FILE=$(FILE) docker-compose up --build --abort-on-container-exit

test-pypi:
	uv run pytest -xvrs --color=yes -m pypi tests/test_pypi_readiness.py

format:
	uv run ruff format .
	uv run ruff check --fix .

publish:
	uv build --no-sources
	UV_PUBLISH_TOKEN="$(PYPI_TOKEN)" uv publish
