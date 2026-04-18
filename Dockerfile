# ----- Builder Stage -----
FROM python:3.14-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /build

COPY requirements.txt .
# Install dependencies in the system python of the builder
RUN uv pip install --system --no-cache -r requirements.txt

# Optionnel: stripper les librairies partagées (.so) pour gagner un peu de place
RUN apt-get update && apt-get install -y --no-install-recommends binutils && \
    find /usr/local/lib/python3.14/site-packages -name "*.so" -exec strip --strip-unneeded {} +

# ----- Final Stage -----
FROM python:3.14-slim

ARG UID=1000

LABEL org.opencontainers.image.source=https://github.com/leolivier/cousins-matter
LABEL org.opencontainers.image.description='Docker image for the Cousins Matter application (https://github.com/leolivier/cousins-matter)'
LABEL org.opencontainers.image.url=https://github.com/leolivier/cousins-matter
LABEL org.opencontainers.image.branch=main
LABEL org.opencontainers.image.licenses=MIT

EXPOSE 9001

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy python dependencies and binaries from builder
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# This is the user that will run the application but through supervisord so 
# we keep running as root for supervisord which will run things as cm_user
RUN adduser --uid ${UID} --disabled-password --gecos "" cm_user && \
		chown -R cm_user:cm_user /app

# now copy all (but .dockerignore rules) with cm_user as proprietary
COPY --chown=cm_user:cm_user . .

ENV USER=cm_user
ENV PORT=9001
ENTRYPOINT ["python", "-m", "scripts.entrypoint"]
CMD ["daphne", "-p", "9001", "-b", "0.0.0.0", "--proxy-headers", "cousinsmatter.asgi:application"]

VOLUME ./data ./media
