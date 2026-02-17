.PHONY: run cpmsg mkmsg up down clean ps logs stop up4run help h u4r test mig mkmig cover

help h:
	@echo "Available targets:"
	@echo "  help, h: Show this help"
	@echo "  run: Run the application outside of docker (supposes postgres, redis and qcluster are running)"
	@echo "  up [c=container_name]: Start the application with docker"
	@echo "  up4run, u4r: Start the docker containers for postgres, redis and qcluster, so you can use run afterwards"
	@echo "  down [c=container_name]: Stop the docker container(s)"
	@echo "  clean: Stop the docker container(s) and remove volumes"
	@echo "  ps [c=container_name]: List the running container(s)"
	@echo "  logs [c=container_name]: Show the logs of the application or the container"
	@echo "  stop [c=container_name]: Stop the application or the container"
	@echo "  mkmsg d=directory: cd to \"directory\" and make messages"
	@echo "  cpmsg d=directory: cd to \"directory\" and compile messages"
	@echo "  mkmig: create a migration"
	@echo "  mig: migrate the database"
	@echo "  test [t=test_name]: run test(s)"
	@echo "  cover [t=test_name]: run test(s) with coverage"

run:
	POSTGRES_HOST=localhost	REDIS_HOST=localhost ./manage.py runserver

up:
	docker compose up -d $(c)

up4run u4r:
	docker compose up -d postgres redis qcluster

down:
	docker compose down $(c)

clean:
	docker compose down --volumes

ps:
	docker compose ps $(c)

logs:
	docker compose logs $(c)

stop:
	docker compose stop $(c)

cpmsg:
	cd "$(d)" && ../manage.py compilemessages

mkmsg:
	cd "$(d)" && ../manage.py makemessages -a

clean:
	docker compose down --volumes

test:
	POSTGRES_HOST=localhost REDIS_HOST=localhost ./manage.py test $(t) $(o)

cover:
	if [ -z "$(t)" ]; then \
		POSTGRES_HOST=localhost REDIS_HOST=localhost coverage run --source="." ./manage.py test $(o); \
	else \
		POSTGRES_HOST=localhost REDIS_HOST=localhost coverage run --source="$(t)" ./manage.py test $(t) $(o); \
	fi
	coverage report --sort=cover --skip-covered -m --fail-under=80 --omit='scripts/*,manage.py,*/asgi.py,*.wsgi.py,*/views_test.py'

mig:
	POSTGRES_HOST=localhost REDIS_HOST=localhost ./manage.py migrate

mkmig:
	POSTGRES_HOST=localhost REDIS_HOST=localhost ./manage.py makemigrations