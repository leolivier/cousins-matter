FROM python:3.12-slim

ARG UID=1000

LABEL org.opencontainers.image.source=https://github.com/leolivier/cousins-matter
LABEL org.opencontainers.image.description='Docker image for the Cousins Matter application (https://github.com/leolivier/cousins-matter)'
LABEL org.opencontainers.image.url=https://github.com/leolivier/cousins-matter
LABEL org.opencontainers.image.branch=main
LABEL org.opencontainers.image.licenses=MIT

EXPOSE 9999

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# install lighttpd for serving static and media files, redis for chat for installing database
# We must update twice as we need first to install gpg before installing redis
RUN apt-get update &&\
		apt-get install -y sudo &&\
		apt-get clean && \
		rm -rf /var/lib/apt/lists/* /var/cache/apt/* /var/cache/debconf/*

# Allows docker to cache installed dependencies between builds
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# This is the user that will run the application but through supervisord so 
# we keep running as root for supervisord which will run things as cm_user
RUN adduser --uid ${UID} --disabled-password --gecos "" cm_user && \
		chown -R cm_user:cm_user /app

# now copy all (but .dockerignore rules) with cm_user as proprietary
COPY --chown=cm_user:cm_user . .

ENV USER=cm_user
ENV PORT=9999
ENTRYPOINT ["./scripts/main_entrypoint.sh"]
CMD ["daphne", "-p", "9999", "-b", "0.0.0.0", "--proxy-headers", "cousinsmatter.asgi:application"]

VOLUME ./data ./media
