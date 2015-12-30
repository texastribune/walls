APP=walls
NS=texastribune

build:
	docker build --tag=${NS}/${APP} .

debug:
	docker run --volumes-from=${APP} --interactive=true --tty=true ${NS}/${APP} bash

run:
	docker run --name=${APP} --detach=true ${NS}/${APP}

interactive: build
	docker run \
		--workdir=/app \
		--volume=$$(pwd):/app \
		--env-file=env \
		--rm --interactive --tty \
		--name=${APP} ${NS}/${APP} bash
