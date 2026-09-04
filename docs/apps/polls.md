---
type: App Reference
title: Polls
description: Polls app (`polls`) — member polls and the event-planning survey submodule (event planners) for scheduling; documented in apps/polls.md
tags: ["app", "polls"]
status: draft
stale_after: 2027-03-05
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-05T00:00:00Z }
---

# Polls

`polls` implements two flavours of the same survey mechanism: plain
**Polls** (yes/no, single/multiple choice, open text, date questions)
and **Event Planners** — an event-planning survey subclass used to pick
a date for an event. Both live in the same app and share models, forms
and vote machinery; the navbar exposes them as separate tabs, gated by
the `show_polls` and `show_event_planners`
[feature flags](/apps/core.md#feature-flags).

**Tenant note:** like [forum](/apps/forum.md), `Poll`, `Question`,
`Answer` subclasses and `EventPlanner` inherit `models.Model` directly —
they are **not** [TenantModel](/apps/tenants.md)-scoped. Polls are
currently shared platform-wide.

## Models (polls/models.py)

- `Poll` — `title`, `description` (500), `owner` FK `Member`,
  `pub_date` (defaults to now), `close_date` (nullable),
  `open_to` (`all` | `act` | `lst`, default active members only) and
  `closed_list` M2M to members, only meaningful when
  `open_to="lst"` — [services.manage_closed_list](polls/services.py)
  raises `ValueError` if a non-closed-list poll carries entries.
- `Question` — `poll` FK (`related_name="questions"`),
  `question_text`, `question_type` and `possible_choices`
  (`JSONField`, list of choices for choice-type questions).
  Types: `YN`, `SC`, `MC`, `OT`, `DT`, plus `SE`/`ME`
  (single/multiple event planning) which are excluded from
  `QUESTION_TYPES` — they are created programmatically, not offered
  in the question form.
- `PollAnswer` — the "ballot": one row per (`poll`, `member`).
  Re-voting updates the same ballot.
- `Answer` (abstract, multi-table inheritance) — `poll_answer` FK to
  the ballot, `question` FK with `related_name="answers_%(class)s"`.
  Concrete subclasses carry the actual `answer` field:
  `YesNoAnswer`, `TextAnswer`, `DateTimeAnswer`, `ChoiceAnswer`,
  `MultiChoiceAnswer` (JSON list), and the event-planner variants
  `SingleEventAnswer(ChoiceAnswer)` / `MultiEventAnswer(MultiChoiceAnswer)`.
  `Answer.set_subclasses()` builds a registry mapping
  `question_type` → answer class (`get_answer_class_for_question_type`);
  `Answer.filter_answers()` fans a filter out over all subclasses and
  drops parent rows shadowed by a child of the same id.
- `QuestionResult` — per-question aggregate built by each subclass's
  static `compute_result` (percentages for yes/no and choices, raw
  value lists for text/dates) plus the requesting user's own answer.
- `EventPlanner(Poll)` — adds `location`, `chosen_date` and the
  `multiple_choices` flag; `get_questions()` excludes the
  event-type question, which is managed separately (see below).

## Event-planning surveys (scheduling)

An `EventPlanner` always has one auto-managed question of type `SE`
or `ME` whose `possible_choices` are the candidate dates:

- `create_event_planner` (polls/services.py) creates it at
  creation time — "Choose one date" or "Choose dates" depending on
  `multichoices_planner` — inside `transaction.atomic()` together with
  the closed list.
- `update_event_planner` reconciles it on edit: if the question was
  already answered, switching single ↔ multiple returns an **error**
  (type is frozen) and merely changing the date list returns a
  **warning** (previous answers may be ignored).

## Who can create, edit, answer

- **Create:** any authenticated member — `PollCreateView.post` sets
  `form.instance.owner = request.user`. Same for event planners.
- **Edit/delete:** owner-or-staff via
  `core.utils.check_edit_permission` on every update/delete path
  (polls, questions, planners). Note `PollUpdateView.form_valid`
  additionally raises `ValueError` if the form instance owner is not
  the requester — a safety net, not the primary check.
- **Answer/vote:** any member can vote; there is **no server-side
  enforcement** of `open_to`/`closed_list` — eligibility is displayed
  (`poll.get_open_to_display`, closed-list members listed) rather than
  enforced. `PollsVoteView.post` reuses the member's existing
  `PollAnswer` and replaces all its answers inside
  `transaction.atomic()` (delete across every answer subclass, then
  save the new ones), so a ballot is never half-written.

## Views and URLs (polls/urls.py, `app_name = "polls"`)

- List views are one class parameterised by `only_published`,
  `show_closed`, `only_closed` and `show_last`
  (polls/views/display_views.py), filtered by
  `get_filtered_polls` (polls/services.py, `pub_date`/`close_date`
  windows, `eventplanner__isnull=True` so polls never list planners)
  and sliced to `show_last or 250`. Variants: open (default, 25),
  all, closed — and the same three under `event-planners/`.
- `polls:<pk>/` detail renders questions **with results** via
  `Poll.get_results`, which prefetches every answer subclass plus its
  `poll_answer` to dodge N+1; `get_poll_answer`
  (polls/services.py) builds a per-question answer cache the same way
  when rendering the vote form.
- CRUD: `create`, `<pk>/update`, `<pk>/delete` (confirm modal),
  questions via `question/create|update|delete` (HTMX
  `HttpResponseClientRefresh`), planners mirrored under
  `event-planners/` by polls/views/event_upsert_views.py subclasses.

## See also

- [Core](/apps/core.md) — `check_edit_permission`, modal confirm, feature flags
- [Members](/apps/members.md) — `Member` as poll owner/ballot holder
- [Tenants](/apps/tenants.md) — scoping model this app does not use yet
