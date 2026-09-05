---
type: Module Reference
title: Notifications
description: How followers notifications become emails — Django-Q2 async execution, immediate vs batched delivery, schedules, and the notification kinds each app produces
tags: ["module", "notifications"]
status: draft
stale_after: 2027-03-05
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-05T11:16:06Z }
---

# Notifications

Everything a member is notified about travels the same road: a content change
calls `core.followers.check_followers`, which either emails "immediate"
recipients right away or stores `NotificationEvent` rows (core/models.py) for
batched members. This fiche covers the execution side; the fan-out itself is
described in [Followers](/modules/followers.md) and
[Core](/apps/core.md#followers-and-notification-batching).

## Execution model: Django-Q2

- Delivery is never done inline in the request: `check_followers` queues
  `core.followers.do_check_followers` with `django_q.tasks.async_task`, and
  `Q_CLUSTER` (config/settings/base.py) runs 2 workers with a 60 s timeout on
  Redis (`REDIS_HOST`/`REDIS_PORT`), `max_attempts: 5`.
- `Q_CLUSTER["sync"] = env.bool("Q_SYNC", False)`; config/settings/dev_base.py
  re-defaults it to **True**, so in development tasks execute synchronously in
  the request (easy to debug, no cluster needed). Set `Q_SYNC=False` locally to
  exercise the real queue.
- In production a `qcluster` process must run — the Docker image ships one
  (make target `make up4run` starts it locally), and `qhealth` hits the
  cluster through a task round-trip.

## Batching

`process_batched_notifications(frequency)` (core/tasks.py) is the batch job:

- selects pending `NotificationEvent`s whose member has
  `email_batch_frequency == frequency`, groups them per member and runs each
  group inside `tenant_context(member.tenant)`;
- drops (deletes) events whose followed object has been deleted
  (`GenericForeignKey` returns `None`) and skips members without an email
  address;
- renders one summary mail per member from
  `core/followers/email-notification-summary.html` (subject includes the
  frequency label and the family `site_name` via
  `tenants.settings_overrides.tenant_setting`), sends it, then deletes the
  processed events — batches are consumed, not marked read.

## Schedules

`setup_notification_schedules()` (core/tasks_schedules.py) is connected to
`post_migrate` by `CousinsMatterConfig.ready` (core/apps.py) and
`get_or_create`s four Django-Q schedules running the batch job for `hourly`,
`daily`, `weekly` and `monthly` (monthly uses `Schedule.MONTHLY`, or a CRON
`0 0 1 * *` fallback). Names are fixed ("Hourly Notifications", ...) and
existing schedules are never overwritten, so manual edits in the Django-Q
admin survive. Setup is skipped during `migrate`/`test`/`collectstatic`
runs.

## Per-app notification kinds

| App | Event | Recipients |
| --- | --- | --- |
| Chat | message posted in a followed room (HTTP view and Channels consumer) | room followers + owner + author's followers |
| Forum | new post; new message or comment on a followed post | post/author followers + owner |
| Members | someone follows you | the followed member (direct email, not batched) |
| Members | death declared for a member | the family's admins (`tenants.authz.admin_or_superusers`) |

Galleries, polls, classified ads, pages, troves and genealogy do not call
`core.followers` today — they would get notifications for free by adding a
`followers` M2M and calling `check_followers`
([Followers](/modules/followers.md)).

# See also

- [Followers](/modules/followers.md) — fan-out rules and `toggle_follow`.
- [Core](/apps/core.md#followers-and-notification-batching) —
  `NotificationEvent` model and batch job details.
- [Conventions](/conventions.md#async-via-django-q2),
  [Architecture](/architecture.md#async-tasks).
- User manual: notification preferences at
  <https://cousins-matter.readthedocs.io/customizing/>.
