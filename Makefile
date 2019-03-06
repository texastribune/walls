APP=walls
NS=texastribune

run: build
	docker-compose run ${APP}

test:
	docker-compose run --entrypoint=py.test ${APP} tests.py

build:
	docker build --tag=${NS}/${APP} .

interactive: build
	docker run \
		--workdir=/app \
		--volume=$$(pwd):/app \
		--env-file=env \
		--rm --interactive --tty \
		--entrypoint=bash \
		--name=${APP} ${NS}/${APP}
