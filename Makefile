APP=walls
NS=texastribune

build:
	docker build --tag=${NS}/${APP} .

debug:
	docker run --volumes-from=${APP} --interactive=true --tty=true ${NS}/${APP} bash

build-dev: build
	docker build -f Dockerfile --tag=${NS}/${APP}:dev .

run:
	docker run --name=${APP} --detach=true --publish=5000:80 ${NS}/${APP}

clean:
	-docker stop ${APP} && docker rm ${APP}
	-docker stop redis && docker rm redis
	-docker stop rabbitmq && docker rm rabbitmq


interactive: build
	docker run \
		--workdir=/app \
		--volume=$$(pwd):/app \
		--env-file=env \
		--rm --interactive --tty \
		--publish=80:5000 \
		--name=${APP} ${NS}/${APP} bash

test: build-dev
	docker run \
		--env-file=env \
		--workdir=/app \
		--rm \
		--entrypoint=python3 \
		texastribune/walls:dev /usr/local/bin/py.test tests.py --cov=.

push:
	docker push ${NS}/${APP}
