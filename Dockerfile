# ----- Builder Stage -----
FROM python:3.14-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
# Install dependencies in a virtual environment at /app/.venv
RUN uv sync --no-group dev

# Optional: strip shared libraries (.so) to save some space
RUN apt-get update && apt-get install -y --no-install-recommends binutils && \
    find /app/.venv -name "*.so" -exec strip --strip-unneeded {} +

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

# pg_dump/pg_restore for the daily database backup. The client major version
# must match the server (18), so install it from the PostgreSQL PGDG repo
# instead of Debian's older client.
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && \
    install -d /usr/share/postgresql-common/pgdg && \
    curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
      -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc && \
    echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $(. /etc/os-release && echo "$VERSION_CODENAME")-pgdg main" \
      > /etc/apt/sources.list.d/pgdg.list && \
    apt-get update && apt-get install -y --no-install-recommends postgresql-client-18 && \
    rm -rf /var/lib/apt/lists/*

# Creates a non-root user with an explicit UID
RUN adduser --uid ${UID} --disabled-password --gecos "" cm_user && \
    chown cm_user:cm_user /app

# Copy python dependencies from builder using cm_user as owner
COPY --from=builder --chown=cm_user:cm_user /app/.venv /app/.venv

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# now copy all (but .dockerignore rules) with cm_user as proprietary
COPY --chown=cm_user:cm_user . .

ENV USER=cm_user
ENV PORT=9001
ENTRYPOINT ["python", "-m", "scripts.entrypoint"]
CMD ["daphne", "-p", "9001", "-b", "0.0.0.0", "--proxy-headers", "cousinsmatter.asgi:application"]

VOLUME ["/app/data", "/app/media"]
