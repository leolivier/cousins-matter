---
name: extract-services-from-views
description: Use when a Django app's views mix business logic (DB queries, model mutations, validation, message/context construction) with HTTP handling and you want to move the non-view logic out into services.py (or a services/ package). Pass the app name as the argument, e.g. /extract-services-from-views forum. Only applies where extraction genuinely simplifies a view — not to every view mechanically.
---

# Extract services from views

## Overview

Move business logic out of Django views into a `services.py` (or `services/` package) so each view
contains **only HTTP/view concerns**. Services take domain objects (`user`, a model instance, a
page, primitives) and return data — **never the `HttpRequest`**.

Reference implementation already exists and is verified: `chat/services.py` (261 lines), extracted
from `chat/views/views_private_rooms.py` + `chat/views/views_room_common.py`. Read it first.

Argument `args` = the app name (e.g. `forum`). Work inside `<app>/`.

## The one rule

> **A service function never takes `request`.** Only domain objects.

If you reach for `request` inside a service, the logic you're holding is HTTP-coupled — it belongs
in the view, not the service. See the table below.

## When to extract — and when to leave it

Extract **only where it genuinely simplifies the view**. The goal is readable, thin views; a
spread of tiny `do_*` functions that just wrap one line is the failure mode.

```
view is genuinely simple (get_object_or_404 + render, or one trivial mutation)?  ──► LEAVE IT
view has real logic: queries, multi-branch mutations,        ──► EXTRACT the logic,
   validation, context-building, error-message construction      keep HTTP in the view
view is a thin wrapper calling other views?                   ──► LEAVE IT
```

**Mutations are business logic, not a view concern.** When you extract, the `.add`/`.remove`/`.save`
go into service functions (`do_*`). They stay inline in the view only as part of a *genuinely
simple* view (the first branch above) — never on the reasoning "it's just a mutation." A mutation
that sits next to a query, a branch, or validation moves to the service with them.

Ask per view, don't blanket-convert a whole file. A 200-line `views.py` may yield one extraction
and five untouched views. That's the right outcome.

## What stays in the view vs moves to services

| Stays in the view (HTTP/view concern) | Moves to services (business logic) |
|---|---|
| `get_object_or_404`, `request.method != "POST"` guard | queryset construction (filters, `annotate`, subqueries) |
| `messages.error/success`, reading `request.POST`/`request.GET` | model mutations (`.add`/`.remove`, `.save`, side-effect orchestration) |
| `redirect(...)`, `render(...)`, `reverse(...)` | validation logic + `ValidationError` handling, error-message construction |
| permission guards that produce a redirect | context dict construction for a template |
| **pagination** (`Paginator.get_page`) — reads `request.GET["page_size"]`, `PageOutOfBounds` carries a redirect URL | deriving fields from data (counts, "owner = first message's author") |
| `check_followers(request, …)` — needs `request.build_absolute_uri` | resolving ids → model objects (e.g. author ids → `Member`) |

The two bolded rows are the trap: they look like logic but are HTTP-coupled. A naive extraction
puts them in the service, the service then needs `request`, and the rule breaks. Keep them in the
view. (`chat/views/views_room_common.py` paginates in the view, then hands the page to
`build_room_context(room, page, private)`.)

## Conventions (match `chat`)

**File:** `<app>/services.py`. When it exceeds ~300–400 lines **or** groups into clearly distinct
domains → split into a package:

```
<app>/services/
  __init__.py      # re-export the public functions, keep imports stable
  members.py
  rooms.py
  ...
```

Existing importers stay `from ..services import do_thing` unchanged.

**Naming / return shapes:**

| Service function | Shape | Example |
|---|---|---|
| `do_<action>(domain_objs…)` — a mutation | returns `(success: bool, message: str)` | `do_add_member_to_private_room(room, user_id)` |
| `get_<thing>_queryset(domain_objs…)` — a query | returns a queryset | `get_chat_rooms_queryset(user, private)` |
| `resolve_<thing>(data)` — an in-place transform | mutates / returns data | `resolve_first_message_authors(rooms)` |
| `build_<thing>_context(domain_objs…)` — template context | returns a dict | `build_room_context(room, page, private)` |

**View orchestration patterns** (kept thin):

```python
# guard that returns a redirect or None — usable as "guard(...) or render(...)"
def not_is_private_admin(request, room):
  if not room.admins.filter(pk=request.user.pk).exists():
    messages.error(request, _("You are not an admin of this private room"))
    return redirect(reverse("chat:private_chat_rooms"))
  return None

# apply a (success, message) service result in one line
def message_result(request, success, message):
  if success:
    messages.success(request, message)
  else:
    messages.error(request, message)

# a mutation view, end to end
room = get_object_or_404(PrivateChatRoom.objects.prefetch_related("followers"), slug=room_slug)
if not_admin := not_is_private_admin(request, room):
  return not_admin
message_result(request, *do_add_member_to_private_room(room, request.POST.get("member-id")))
return redirect(reverse("chat:private_room_members", args=[room.slug]))
```

**Extraction that keeps `request` out** — the view extracts the few things the service needs and
builds URLs itself; the service never sees `request`:

```python
# view: HTTP concerns only — decode POST, build URL, notify followers (needs request)
room_name = unquote(request.POST["name"])
new_room, created, errors = do_create_chat_room(request.user, room_name, private)
for error in errors:
  messages.error(request, error)
if new_room is None:
  return redirect(reverse("chat:private_chat_rooms") if private else reverse("chat:chat_rooms"))
room_url = reverse("chat:private_room" if private else "chat:room", args=[new_room.slug])
if created and not private:
  check_followers(request, followed_object=new_room, followed_object_owner=request.user, followed_object_url=room_url)
return redirect(room_url)
```

## Process

1. `cd <app>/views` (or `<app>` if views are in `views.py`). Skim each view; tag the ones with real
   business logic (per the table). Skip the thin/HTTP-only ones.
2. For each tagged view: split concerns onto paper — left column HTTP, right column logic. If the
   right column is small, leave the view alone.
3. Move right-column logic into `<app>/services.py` following the naming table. Services take
   domain objects, return data; **no `request`**. If a piece needs `request`, it stays in the view.
4. Rewrite the view to orchestrate: fetch + guard + call service + `messages`/`render`/`redirect`.
   Reuse `message_result` / `not_is_<role>` helpers across views in the same file.
5. Update the view's imports (drop the model/query imports that moved; services carries them).
6. **Verify before declaring done** (see below).

## Verify

```bash
source .venv/bin/activate
ruff check <app>/services.py <app>/views/          # no unused imports; eyeball that no service takes `request`
# `--noinput` avoids the test-DB "Type 'yes'" prompt on re-runs (EOFError in a pipe — see Gotchas)
ENVIRONMENT="test" ./manage.py test --noinput --exclude-tag=ui <app>.tests.<module>   # e.g. chat.tests.tests_private
ENVIRONMENT="test" ./manage.py test --noinput --tag=ui <app>.tests.ui.<module>        # e.g. forum.tests.ui.tests_ui_posts
```

Expected: `ruff` clean, non-UI **and** UI tests green. If a message string or its level changed,
update the test's `assertContainsMessage` — don't silently change user-facing wording. (A `429`
from `ipapi.co` during UI runs is an external geolocation API rate-limiting — non-fatal; trust the
final `Ran N tests … OK` line.)

## Gotchas

- **Don't move pagination into a service.** `Paginator.get_page` reads `request.GET` and
  `PageOutOfBounds` is built from a redirect URL — both HTTP. The view paginates, then hands the
  page to a `build_*_context` service. (See `list_chat_rooms` / `display_chat_room`.)
- **`check_followers` stays in the view** — it needs `request.build_absolute_uri` for the email
  link. The service returns the created room + a `created` flag; the view decides whether to notify.
- **Preserve message wording and level exactly** during extraction. `chat`'s refactor moved some
  `messages.warning` → `messages.error` (services return a single `(success, message)`); each such
  change required a matching test update. Keep behavior unless you intend to change it, and update
  the test in the same diff.
- **Avoid circular imports.** `views_room_common` is imported by `views_private_rooms`, so helpers
  like `not_is_private_member` can't be shared back across that edge — keep guards local to the
  file that needs them.
- **`@.EXPORT_ALL_VARIABLES` Makefile needs the venv active** — `make test`/`make check` fail with
  `No module named django` if you forget `source .venv/bin/activate`. (Run `./manage.py` directly as
  above to sidestep.)
- **Pass `--noinput` to `./manage.py test`.** A second run in the same session finds the test DB
  already created and prompts "Type 'yes' to delete it" — in a non-interactive (piped) shell that's
  an `EOFError` and the run aborts before any test. `--noinput` autoclobbers; `--keepdb` reuses the
  DB (faster, but masks migration changes).
