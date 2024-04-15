FROM python:3.12-slim

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

VOLUME [ "/app/data" ]
VOLUME [ "/app/media" ]
