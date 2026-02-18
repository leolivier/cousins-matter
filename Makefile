.PHONY: run cpmsg mkmsg up down clean ps logs stop up4run help h u4r test mig mkmig cover minify

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
	@echo "  mkmsg a=application: cd to \"application\" and make messages"
	@echo "  cpmsg a=application: cd to \"application\" and compile messages"
	@echo "  mkmig: create a migration"
	@echo "  mig: migrate the database"
	@echo "  test [t=test_name]: run test(s)"
	@echo "  cover [a=application] [co=coverage_options] [to=test_options]: run test(s) with coverage. Default is all applications. If an application is given, the coverage result is stored in .coverage.<application>."
	@echo "  minify [a=application]: minify the css and js files of an application. Default is all applications."

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
	cd "$(a)" && ../manage.py compilemessages

mkmsg:
	cd "$(a)" && ../manage.py makemessages -a

clean:
	docker compose down --volumes

test:
	POSTGRES_HOST=localhost REDIS_HOST=localhost ./manage.py test $(t) $(o)

cover:
	if [ -z "$(a)" ]; then \
	  df=.coverage; \
		POSTGRES_HOST=localhost REDIS_HOST=localhost coverage run --source="." $(co) ./manage.py test $(to); \
	else \
	  df=.coverage.$(a); \
		POSTGRES_HOST=localhost REDIS_HOST=localhost coverage run --source="$(a)" $(co) ./manage.py test $(to); \
	fi; \
	coverage report --sort=cover --skip-covered -m --fail-under=80 --omit='scripts/*,manage.py,cousinsmatter/asgi.py,cousinsmatter/wsgi.py,cousinsmatter/htmlvalidator.py,*/views_test.py,*/migrations/*,*/tests/*' --data-file=$(df)

mig:
	POSTGRES_HOST=localhost REDIS_HOST=localhost ./manage.py migrate

mkmig:
	POSTGRES_HOST=localhost REDIS_HOST=localhost ./manage.py makemigrations

minify:
	app="$(a)"; \
	if [ -z "$$app" ]; then app="."; fi; \
	css-html-js-minify $$app