---
type: App Reference
title: Chat
description: Real-time chat rooms over Django Channels — public and private rooms, websocket consumer, read receipts, follower notifications
tags: ["app", "chat"]
status: draft
stale_after: 2027-03-04
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-04T12:00:00Z }
---

# Chat

`chat` provides real-time rooms built on **Django Channels**: HTTP
views list/create rooms and render history, while a websocket consumer
(create/update/delete messages, read receipts) pushes updates to
everyone in a room. Rooms and messages are
[TenantModel](/apps/tenants.md)-scoped. Navbar visibility is gated by
the `show_public_chats` / `show_private_chats`
[feature flags](/apps/core.md#feature-flags-and-context-processors).

## Models (chat/models.py)

- `ChatRoom` (`TenantModel`) — `name`, `slug` (slugified in
  `clean()`, unique per tenant via
  `(tenant, slug)` `UniqueConstraint`), `followers` M2M to active
  members (`related_name="followed_chat_rooms"`). `objects` is a
  `ChatRoomManager` with `public()` / `private()` (and async
  `apublic()`/`aprivate()`) variants filtering on the
  `privatechatroom` reverse relation. Convenience accessors
  (`first_message`, `last_message`, `owner` = author of the first
  message, `is_public`) all have `a`-prefixed async twins because the
  consumer runs on the event loop.
- `PrivateChatRoom` — multi-table child of `ChatRoom` adding
  `admins` M2M. It **redeclares `objects = ChatRoomManager()`**:
  without it Django would fall back to a plain (unscoped) manager on
  the child and private-room lookups would cross tenants. `members()`
  is `followers`; helpers `add_member`/`remove_member`.
- `ChatMessage` (`TenantModel`) — `member`, `room`, `content`
  (up to 2 MiB), `date_added`/`date_modified`, and `read_by` M2M
  (private-room recipients who read it; the sender is never added).
  `compute_status()` is a pure function deriving the sender's view of
  a message — `MessageStatus.UNREAD` / `PARTIALLY_READ` / `READ` —
  from `(is_public, room_members_count, read_count, sender_is_member)`;
  it is shared by views, the consumer and tests so the derivation is
  identical everywhere (and callable on prefetched data to avoid N+1).

**Public vs private** is structural: a room is public unless a
`PrivateChatRoom` row exists for it (MTI). Private rooms restrict
membership (`followers`) and expose admins; public rooms are visible
to every member of the tenant.

## Channels plumbing

- ASGI: `cousinsmatter/asgi.py` (`ASGI_APPLICATION`), channel layer
  `channels_redis.core.RedisChannelLayer` on Redis
  (config/settings/base.py; `socket_timeout` is deliberately `None`
  to avoid racing channels-redis' `BZPOPMIN`).
- Routing (chat/routing.py): `websocket_urlpatterns` maps
  `chat/ws/<str:room_slug>` to `ChatConsumer` — a single consumer for
  public and private rooms.
- Group name is **tenant-prefixed**:
  `chat_<tenant_id>_<room_slug>` (consumers.py `connect`). Slugs are
  only unique per tenant, so without the prefix two families' rooms
  with the same slug would broadcast into each other. Platform
  superusers connect unscoped (`tenant_id = None`).
- The request-bound thread-local tenant does **not** survive into the
  threads async ORM uses, so every consumer DB access re-enters
  `tenant_context(self._tenant())` inside a `sync_to_async` helper
  (`_aget_room`, `_aget_message`, previous-message lookup).

### `ChatConsumer` (chat/consumers.py)

- `connect` — joins the room group; in private rooms marks all
  previously received messages read for the connecting user and
  broadcasts a `read_status_update`.
- `receive` dispatches JSON `{action, args}` to
  `create_chat_message`, `update_chat_message`,
  `delete_chat_message`; unknown actions raise.
- `receive_create_chat_message` — saves the message
  (`acreate_message`, tenant-checked; unknown room → `error` frame
  "Room not found in family"), then `group_send`s the event; each
  consumer renders the message fragment server-side
  (`chat/room_detail.html#message_div`) and sends it to its own
  websocket. Delete is soft: content is replaced by a
  "This message has been deleted" notice.
- `check_user_permission` — only the author may edit/delete, and a
  message belonging to another tenant is refused (returns `error`
  frames rather than mutating).
- Read receipts: `_mark_room_read` bulk-inserts `read_by` through
  rows with `ignore_conflicts=True` (concurrent readers race safely),
  `_broadcast_read_status` recomputes statuses from the DB and emits
  one grouped `read_status_update` so the sender's ✓ flips to ✓✓.

## Notifications (chat side effects)

- Each new message notifies the **room owner's** followers:
  `acreate_message` calls `core.followers.check_followers` with
  `request=None` (no HTTP request in a consumer) and a URL built from
  the websocket `Origin` header (`_build_absolute_url`).
- Creating a **public** room notifies the creator's followers from
  the view (`create_chat_room` in chat/views/views_room_common.py,
  shared by the public and private creation views), which *does* have
  the request — `do_create_chat_room` deliberately leaves it to the
  caller. Private rooms do not notify (members are invited
  explicitly).

## Services (chat/services.py)

- `do_create_chat_room(user, name, private)` — `get_or_create` in
  one `transaction.atomic()`, creator added as member (and admin for
  private rooms), slug-collision errors turned into friendly messages;
  returns `(new_room, created, errors)`.
- Private-room membership invariants:
  `do_remove_member_from_private_room` / `do_remove_admin_...`
  refuse to remove the last member or the last admin, and removals
  commit atomically; `do_add_member_to_private_room`,
  `do_add_admin_to_private_room` (only members can become admins).
- `get_chat_rooms_queryset(user, private)` — public or
  mine-only-private listing annotated with message/follower counts,
  first-message author and `is_following`.
  `resolve_first_message_authors()` bulk-fetches the authors.
- `get_room_messages()` / `build_room_context()` — history with
  `read_by` prefetched and a per-message read-status map computed via
  `compute_status` (avoids the N+1 of calling `read_status()` per
  message).

## Views and URLs (chat/urls.py, `app_name = "chat"`)

Public rooms: `""` (+ pagination), `room` (create),
`room/<slug>` (+ page), `toggle-follow`, `edit`, `delete`.
Private rooms under `private/`: listing, create, display, and
membership management (`add_member/`, `add_admin/`,
`remove_member/<username>`, `remove_admin/<username>`, `leave/`,
`admin_leave/`, `members/`, `admins/`, `search_members`).
`settings.DEBUG`-only `test/` endpoints generate rooms/messages.

## See also

- [Core](/apps/core.md) — followers machinery (`check_followers` with `request=None`), feature flags
- [Tenants](/apps/tenants.md) — `tenant_context` inside the consumer, tenant-prefixed Channels groups
- [Notifications](/modules/notifications.md) — how chat notifications are batched
- [Architecture](/architecture.md) — ASGI/Channels deployment notes
