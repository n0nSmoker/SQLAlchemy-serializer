.PHONY: test format test-pypi
FILE = $(file)

test:
	TEST_FILE=$(FILE) docker-compose up --build --abort-on-container-exit

test-pypi:
	uv run pytest -xvrs --color=yes -m pypi tests/test_pypi_readiness.py::test_pypi_version_can_be_installed_and_used

format:
	uv run ruff format .
	uv run ruff check --fix .

publish:
	uv build --no-sources
	UV_PUBLISH_TOKEN="$(PYPI_TOKEN)" uv publish
