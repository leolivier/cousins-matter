---
type: App Reference
title: Forum
description: Discussion forum — posts with replies (messages) and comments, follower subscriptions with notifications on new content
tags: ["app", "forum"]
status: draft
stale_after: 2027-03-04
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-04T22:23:24Z }
---

# Forum

`forum` is a classic thread model: a `Post` opens a thread with a
first `Message`, other members reply with further `Message`s, and
replies can be commented. Subscribing to a post ("follow") drives
email/in-app notifications through the generic
[followers machinery](/apps/core.md#followers-and-notification-batching).
Navbar visibility is gated by the `show_forums`
[feature flag](/apps/core.md#feature-flags-and-context-processors).

**Tenant note:** unlike most content apps, `Post`, `Message` and
`Comment` inherit `models.Model` directly — they are **not**
[TenantModel](/apps/tenants.md)-scoped (no `tenant` field, no
`TenantManager`). Forum content is currently shared platform-wide;
passing through `tenants.scoping` has not been applied to this app yet.

## Models (forum/models.py)

- `Message` — `author` FK `Member`, `content`
  (`max_length=settings.MESSAGE_MAX_SIZE`, config/settings/base.py),
  nullable `post` FK (the first message is created before its post),
  `created`/`modified` timestamps.
- `Post` — `title`, `first_message` FK (`related_name="first_of_post"`,
  author of it is the post **owner** via the `owner` property),
  `followers` M2M to active members (`related_name="followed_posts"`)
  — this is the subscription list.
- `Comment` — `author` FK, `message` FK (a comment attaches to a
  reply `Message`), `content` capped by
  `MESSAGE_COMMENTS_MAX_SIZE` (400).

## Notifications on new content (forum/views/views_follow.py)

Thin wrappers over [core.followers](/apps/core.md), each passing the
canonical post URL `reverse("forum:display", post_id)`:

- `check_followers_on_new_post(request, post)` — after creating a
  post, notify the **author's** followers
  (`check_followers(request, post, request.user, url)`, no
  `new_object`).
- `check_followers_on_message(request, message)` — a reply notifies
  the post's followers **plus** the owner's followers
  (`new_internal_object=message`, `author=message.author`).
- `check_followers_on_comment(request, comment)` — same with the
  comment as the new object.

Batching (immediate email vs `NotificationEvent` rows) is decided by
each recipient's `email_batch_frequency`
([Members](/apps/members.md) /
[Notifications](/modules/notifications.md)).

## Subscription (follow/unfollow)

`toggle_follow` view (`<int:pk>/toggle-follow`, name
`forum:toggle_follow`) delegates to `followers.toggle_follow`, which
toggles the current member in `Post.followers` and answers HTMX with
the refreshed button. That same M2M is the notification recipient
list: `core.followers` reads `followed_object.followers` by
convention, so following a post is what subscribes you to it.

## Views and URLs (forum/urls.py, `app_name = "forum"`)

- `""` / `page/<int:page>` — `PostsListView` on
  `get_posts_list_queryset()` (forum/services.py): message and
  follower counts annotated with `distinct=True` (two aggregates in
  one queryset would cross-join and inflate both), most recent first;
  paginated by `core.utils.Paginator` with
  `DEFAULT_POSTS_PER_PAGE` (25).
- `create` — `PostCreateView` builds title + first-message forms and
  saves them through `do_create_post()` (forum/services.py), which
  writes message → post → back-link to the message inside
  `transaction.atomic()`; on failure the view deletes any partially
  saved rows. Notification happens only after the atomic block
  succeeds (it needs the request). Oversized bodies are answered with
  a 400 (`RequestDataTooBig`).
- `<int:pk>` (+ `/page_num`) — `PostDisplayView` renders the first
  message plus paginated replies from `get_post_replies_queryset()`
  (replies only, author and comments prefetched).
- `edit`, `delete` — `check_edit_permission` (owner or staff,
  core.utils); delete goes through `confirm_delete_modal` and cascades
  to replies and comments.
- Replies: `<int:pk>/reply`, `edit_reply`, `delete_reply`; comments:
  `<int:message_id>/comments`, `edit_comment`, `delete_comment` —
  creation paths call the matching `check_followers_on_*` helper.
- `settings.DEBUG`-only test endpoints under `test/`
  (`views_test.py`) to generate posts/replies/comments.

## See also

- [Core](/apps/core.md) — followers/batching machinery, pagination and modal helpers
- [Members](/apps/members.md) — `Member.followed_posts`, `email_batch_frequency`
- [Notifications](/modules/notifications.md) — batched notification lifecycle
- [Tenants](/apps/tenants.md) — why forum is the odd one out (not tenant-scoped yet)
