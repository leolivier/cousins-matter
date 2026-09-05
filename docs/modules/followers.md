---
type: Module Reference
title: Followers
description: Generic follow/unfollow machinery in core/followers.py — what any model needs to be followable, what a follow triggers, and who gets emailed
tags: ["module", "followers"]
status: draft
stale_after: 2027-03-05
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-05T11:16:06Z }
---

# Followers

"Following" is generic: any model with a `followers` `ManyToManyField` to
`Member` can be followed, and `core/followers.py` turns "something new was
added to a followed object" into emails and batched notification events. The
whole machinery lives in one module — there is no per-app notification code
beyond the call sites.

## The API (core/followers.py)

- `check_followers(request, followed_object, followed_object_owner,
  followed_object_url, new_internal_object=None, author=None)` — entry point
  called by content apps after creating an object. Builds the absolute URL
  from the request, then dispatches the real work as a Django-Q task
  (`async_task("core.followers.do_check_followers", ...)`, hook
  `post_check_followers`). The owner's `tenant_id` is passed explicitly
  because the Q worker has no request/middleware to resolve a tenant from.
- `do_check_followers(...)` — the task body. Runs inside
  `tenant_context(Tenant(pk=tenant_id))` (tenants/scoping.py) and:
  1. unions the recipients: `followed_object.followers` + the owner's own
     followers + the owner + the author's followers (each `.only(...)`
     restricted to the fields used),
  2. discards the author (you are never notified about your own post),
  3. splits by `Member.email_batch_frequency`
     ([Members](/apps/members.md#the-member-model)): `never` → skipped,
     `immediate` → emailed now, anything else → one `NotificationEvent` row
     (core/models.py) for the batch job.
- `generate_emails(followed_object, owner, new_internal_object, author, url,
  follower_emails)` — one `EmailMultiAlternatives` with all immediate
  recipients in `bcc`, HTML alternative rendered from
  `core/followers/email-followers-on-change.html`; wording differs for a
  creation vs "added to". Raises `ValueError` if `str(followed_object)` is
  empty — followed objects must have a usable name.
- `toggle_follow(request, followed_object, owner, followed_object_url)` —
  follow/unfollow entry point: adds/removes `request.user` in
  `followed_object.followers`, flashes a message, and on *follow* (not when
  following yourself) emails the object's owner from
  `core/followers/new_follower.html`. Returns a redirect to
  `followed_object_url`.

## What a follow triggers

1. Immediately: a "new follower" email to the object's owner (unless the
   follower is the owner).
2. On later content: `check_followers` → immediate emails and/or
   `NotificationEvent` rows → batch summary emails
   ([Notifications](/modules/notifications.md)).

## What a model needs to be followable

- a `followers = models.ManyToManyField(settings.AUTH_USER_MODEL, ...)`
  (see `Member.followers`, members/models.py; `ChatRoom.followers`;
  forum `Post.followers`),
- a non-empty `str()` (used as the object name in emails), and
- ideally a `_meta.verbose_name` (used as the object type in wording).

## Call sites

- Chat: follow/unfollow of public rooms
  (chat/views/views_public_rooms.py, URL `chat:toggle_follow`);
  `check_followers` on new messages from both the HTTP view
  (chat/views/views_room_common.py) and the Channels consumer
  (chat/consumers.py — passes `request=None`, so the URL must already be
  absolute).
- Forum: `forum/views/views_follow.py` wraps `toggle_follow` plus three
  `check_followers` variants — new post (followers of the author), new
  message on a followed post, new comment on a followed post.
- Members: people-to-people follow is *not* `core.followers` —
  `members/views/views_followers.py` → `do_toggle_follow`
  (members/services/members.py) edits `Member.followers` directly and emails
  the followed member ([Members](/apps/members.md#following)).

# See also

- [Core](/apps/core.md#followers-and-notification-batching) — model
  `NotificationEvent` and the batch job.
- [Notifications](/modules/notifications.md) — async execution, schedules,
  per-app kinds.
- [Chat](/apps/chat.md#notifications-chat-side-effects),
  [Forum](/apps/forum.md#notifications-on-new-content-forumviewsviews_followpy).
- [Conventions](/conventions.md#followers-drive-notifications).
- User manual: notification preferences at
  <https://cousins-matter.readthedocs.io/customizing/>.
