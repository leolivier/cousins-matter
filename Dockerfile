FROM python:3.12-slim

ARG USER=cm_user
ARG UID=5678
ARG APP_DIR=/app

LABEL org.opencontainers.image.source=https://github.com/leolivier/cousins-matter
LABEL org.opencontainers.image.description='Docker image for the Cousins Matter application (https://github.com/leolivier/cousins-matter)'
LABEL org.opencontainers.image.url=https://github.com/leolivier/cousins-matter
LABEL org.opencontainers.image.branch=main
LABEL org.opencontainers.image.licenses=MIT

EXPOSE 8000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

WORKDIR ${APP_DIR}

# install lighttpd for serving static and media files, redis for chat, sqlite3 for installing database
# We must update twice as we need first to install gpg before installing redis
RUN apt-get update &&\
		apt-get install -y lighttpd lsb-release curl gpg sqlite3 sudo supervisor cron && \
		curl -fsSL https://packages.redis.io/gpg | gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg &&\
		echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" > /etc/apt/sources.list.d/redis.list &&\
		apt-get update &&\
		apt-get install -y redis	&&\
		mkdir -p "/var/log/supervisord" "/var/run/supervisord" &&\
		rm -rf /var/lib/apt/lists/*

# Allows docker to cache installed dependencies between builds
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# This is the user that will run the application but through supervisord so 
# we keep running as root for supervisord which will run things as $USER
RUN adduser --uid ${UID} --disabled-password --gecos "" ${USER} && \
		chown -R ${USER}:${USER} ${APP_DIR}

# now copy all (but .dockerignore rules) with $USER as proprietary
COPY --chown=${USER}:${USER} . .
# manage crontab
COPY scripts/crontab.txt /etc/cron.d/cm_crontab
RUN chmod 0644 /etc/cron.d/cm_crontab && crontab /etc/cron.d/cm_crontab

ENV USER=${USER}
ENV APP_DIR=${APP_DIR}
# runs the production server (as root)
ENTRYPOINT ["./scripts/entrypoint.sh"]
# supervisord must run as root
CMD ["supervisord", "-c", "./supervisord.conf"]

VOLUME ./data ./media
