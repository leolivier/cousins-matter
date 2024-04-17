FROM python:3.12-slim

LABEL org.opencontainers.image.source=https://github.com/leolivier/cousins-matter
LABEL org.opencontainers.image.description='Docker image for the Cousins Matter application (https://github.com/leolivier/cousins-matter)'
LABEL org.opencontainers.image.url=https://github.com/leolivier/cousins-matter
LABEL org.opencontainers.image.branch=main
LABEL org.opencontainers.image.licenses=MIT

WORKDIR /app
# install lighttpd for serving static and media files
RUN apt-get update &&\
		apt-get install -y lighttpd &&\
		rm -rf /var/lib/apt/lists/*

# Allows docker to cache installed dependencies between builds
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# runs the production server
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["supervisord", "-c", "/app/supervisord.conf"]

VOLUME [ "/app/data" ]
VOLUME [ "/app/media" ]
