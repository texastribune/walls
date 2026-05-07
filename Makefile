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

# Build and push the production image. Forces linux/amd64 because the
# production cron runner is x86; on Apple Silicon a plain `docker push`
# would upload an arm64 image and silently break the next cron run.
push:
	docker buildx build --platform linux/amd64 \
		--tag=${NS}/${APP}:latest \
		--push .
