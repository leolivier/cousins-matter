.PHONY: run cpmsg mkmsg up down ps logs stop up4run help h u4r

help, h:
	@echo "Available targets:"
	@echo "  help, h: Show this help"
	@echo "  run: Run the application outside of docker (supposes postgres, redis and qcluster are running)"
	@echo "  up: Start the application with docker (pass c=container_name to target a specific container)"
	@echo "  up4run, u4r: Start the docker containers for postgres, redis and qcluster, so you can use run afterwards"
	@echo "  down: Stop the docker containers (pass c=container_name to target a specific container)"
	@echo "  ps: List the running containers (pass c=container_name to target a specific container)"
	@echo "  logs: Show the logs of the application (pass c=container_name to target a specific container)"
	@echo "  stop: Stop the application (pass c=container_name to target a specific container)"
	@echo "  cpmsg: pass d=directory to target a specific directory, then cd to this directory and compile messages"
	@echo "  mkmsg: pass d=directory to target a specific directory, then cd to this directory and make messages"

run:
	export POSTGRES_HOST=localhost && export REDIS_HOST=localhost && ./manage.py runserver

up:
	docker compose up -d $(c)

up4run, u4r:
	docker compose up -d postgres redis qcluster

down:
	docker compose down $(c)

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