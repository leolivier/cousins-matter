# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cousins Matter is a self-hosted Django application for managing large families. It provides member management, photo galleries, forums, chat rooms, polls, classified ads, genealogy tracking, and a basic CMS.

## Tech Stack

- **Framework**: Django 6.x with Django Channels for WebSockets
- **Python**: 3.14+
- **Database**: PostgreSQL (production), SQLite supported for dev
- **Cache/Task Queue**: Redis with Django-Q2
- **Frontend**: Bulma CSS framework, HTMX, crispy-forms
- **ASGI Server**: Daphne
- **Static Files**: WhiteNoise (CompressedManifestStaticFilesStorage)
- **Container**: Docker with Docker Compose

## Development Commands

Activate the virtual environment first:
```bash
source .venv/bin/activate
```

All common commands are available via the Makefile:

```bash
# Setup and run locally (requires postgres/redis running)
make up4run          # Start postgres, redis, qcluster containers
make run             # Run Django dev server on port 8000

# Docker operations
make up              # Start all containers with docker-compose
make down            # Stop containers
make clean           # Stop and remove volumes
make logs            # Show container logs

# Testing
make test            # Run all tests
make test t=<test>   # Run specific test (e.g., make test t=members.tests.tests_member)
make cover           # Run tests with coverage report (80% minimum)
make cover a=<app>   # Coverage for specific app only

# Database
make mkmig           # Create migrations
make mig             # Apply migrations

# Code quality
make check           # Run ruff format, ruff check, and mypy

# Translations
make mkmsg a=<app>   # Make messages for an app
make cpmsg a=<app>   # Compile messages for an app

# Other
make shell           # Django shell
make minify          # Minify CSS/JS files
```

## Project Architecture

### Settings Structure

Settings are split by environment in `config/settings/`:
- `base.py` - Common settings loaded by all environments
- `development.py` - Local development (DEBUG=True, console email backend)
- `production.py` - Production settings
- `local_test.py` - Local test running
- `docker_devt.py` / `docker_test.py` - Docker-based development/testing

The active environment is controlled by the `ENVIRONMENT` env variable (defaults to "production").

### Application Structure

The project follows standard Django multi-app architecture:

- **core** - Base utilities, shared templates, context processors, middleware
- **members** - User management (custom Member model replacing User), profiles, authentication, CSV import/export
- **chat** - WebSocket-based chat (public/private rooms) using Django Channels
- **forum** - Forum posts and replies with notifications
- **galleries** - Photo/video galleries with bulk upload
- **polls** - Polls and event planning surveys
- **classified_ads** - Classified advertisements
- **pages** - CMS flatpages with custom editing
- **troves** - Family treasures (texts, music, videos)
- **genealogy** - GEDCOM import/export, family charts

### Key Architectural Patterns

1. **Custom User Model**: `members.models.Member` extends AbstractUser with family-related fields. Always use `get_user_model()` or `Member` directly.

2. **Feature Flags**: Features can be enabled/disabled via `FEATURES_FLAGS` dict in settings. Check `core.context_processors.features`.

3. **Protected Media**: Media files are served through a protected endpoint (`/protected_media/`) with access control, not directly. Public media goes in `/media/public/`.

4. **Followers System**: Members can follow each other via `core.followers` utilities for notifications.

5. **Async Tasks**: Background tasks (emails, notifications) use Django-Q2 configured to run synchronously in dev (`Q_SYNC=True`).

6. **WebSockets**: Chat uses Django Channels with Redis as the channel layer. See `chat/consumers.py` and `chat/routing.py`.

7. **OAuth**: django-allauth is configured for Google, Facebook, Apple, GitHub, PocketID, and generic OpenID Connect.

## Testing

- Tests are in `<app>/tests/` directories
- Base test classes in `members/tests/tests_member_base.py` provide `MemberTestCase` with helper methods for creating test users
- Tests require postgres and redis running (use `make up4run`)
- Coverage minimum is 80%
- Run specific tests: `make test t=members.tests.tests_member.UsersManagersTests.test_create_member`

## Docker Architecture

Static files are served via WhiteNoise in the Django container (no separate web server needed for statics in development).

The Docker Compose setup includes:
- `cousins-matter` - Main Django/Daphne application (port 9005:9001)
- `qcluster` - Django-Q2 task worker
- `postgres` - PostgreSQL database (port 5432)
- `redis` - Redis for cache and channels (port 6379)
- `nginx` - Reverse proxy for static/media files (port 8000)

## Important Files

- `.env` - Environment configuration (copy from `.env.example`)
- `manage.py` - Points to `core.settings` (not cousinsmatter.settings)
- `cousinsmatter/asgi.py` - ASGI application with Channels routing
- `scripts/entrypoint.py` - Docker container initialization
- `scripts/manage_cousins_matter.py` - Installation/management CLI

## Code Style

- Line length: 127 characters
- Indent: 2 spaces
- Linting: ruff (configured in `ruff.toml`)
- Type checking: mypy (excludes migrations)

## Translations

Supported languages: English, French, Spanish, German, Italian, Portuguese.
Translation files in each app's `locale/` directory.

## Documentation

MkDocs documentation in `docs/` directory.
Build/serve: `mkdocs serve` / `mkdocs build`
