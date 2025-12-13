.PHONY: test format
FILE = $(file)

test:
	TEST_FILE=$(FILE) docker-compose up --build --abort-on-container-exit

format:
	uv run ruff format .
	uv run ruff check --fix .
