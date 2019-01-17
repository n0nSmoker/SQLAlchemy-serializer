.PHONY: test

test:
	docker-compose up --build --abort-on-container-exit
