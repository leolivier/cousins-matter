# Tenant Join Request Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Family-scoped anonymous pages (`/<slug>/`, `/<slug>/join/`) that route registration requests to the tenant's admins, with one code path serving `MULTI_TENANT_ENABLED=False` via the default tenant.

**Architecture:** A shared `resolve_join_tenant()` helper resolves the tenant (URL slug, or default tenant when tenancy is off). `TenantHomeView` renders the same `LoginView` as `members:login` under tenant context; `TenantJoinRequestView` (replacing `RegistrationRequestView`) emails `admin_or_superusers(tenant)` with the existing prefilled invite link. Routes are always mounted, last in the URLconf.

**Tech Stack:** Django 5, django-simple-captcha, existing `tenants` app primitives (`scoping`, `authz`, `settings_overrides`), Bulma templates.

**Spec:** `docs/superpowers/specs/2026-09-09-tenant-join-request-design.md`

## Global Constraints

- Python/Django repo; **2-space indent** everywhere (match existing files).
- `make check` (ruff format + ruff check + pyright) must pass before every commit.
- Tests: `make test t=<dotted.module>`; UI: `make test-ui t=<module>`.
- **Never import from the `saas` app** (upstream-safe code); the throttle is reimplemented locally.
- UI strings always via gettext (`_()` / `{% translate %}`); code and comments in English.
- Work on branch `feature/tenant-join-request` (already checked out).
- Route names produced here and consumed by templates: `tenant-home`, `tenant-join` (root URLconf, no namespace), plus kept `members:register_request` (alias).
- Helper produced here: `tenants.services.resolve_join_tenant(slug: str | None) -> Tenant | None`.

---

### Task 1: `resolve_join_tenant` helper

**Files:**
- Modify: `tenants/services.py` (append function; ensure `from django.conf import settings` is in the module imports)
- Test: `tenants/tests/tests_join_flow.py` (create)

**Interfaces:**
- Consumes: `Tenant.get_default()` (exists, `tenants/models.py:63`), `Tenant.objects` manager.
- Produces: `resolve_join_tenant(slug: str | None) -> Tenant | None` — `None` = caller raises 404. Used by Tasks 2 and 3.

- [ ] **Step 1: Write failing tests**

Create `tenants/tests/tests_join_flow.py`:

```python
from django.conf import settings
from django.test import override_settings

from members.tests.tests_member_base import MemberTestCase

from ..models import Tenant, TenantSettings


class ResolveJoinTenantTests(MemberTestCase):
  """Unit tests for tenants.services.resolve_join_tenant."""

  def resolve(self, slug):
    from ..services import resolve_join_tenant

    return resolve_join_tenant(slug)

  def test_none_slug_resolves_default_tenant(self):
    self.assertEqual(self.resolve(None).pk, Tenant.get_default().pk)

  @override_settings(MULTI_TENANT_ENABLED=True)
  def test_valid_slug_resolves_tenant(self):
    tenant = Tenant.objects.create(name="Famille Dubois", slug="famille-dubois")
    self.assertEqual(self.resolve("famille-dubois").pk, tenant.pk)

  @override_settings(MULTI_TENANT_ENABLED=True)
  def test_unknown_slug_is_none(self):
    self.assertIsNone(self.resolve("inconnu"))

  @override_settings(MULTI_TENANT_ENABLED=True)
  def test_inactive_tenant_is_none(self):
    tenant = Tenant.objects.create(name="Ghost", slug="ghost", is_active=False)
    self.assertIsNone(self.resolve(tenant.slug))

  @override_settings(MULTI_TENANT_ENABLED=False)
  def test_flag_off_other_slug_is_none(self):
    Tenant.objects.create(name="Other", slug="other")
    self.assertIsNone(self.resolve("other"))

  @override_settings(MULTI_TENANT_ENABLED=False)
  def test_flag_off_default_slug_resolves(self):
    self.assertEqual(self.resolve(Tenant.get_default().slug).pk, Tenant.get_default().pk)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `make test t=tenants.tests.tests_join_flow`
Expected: FAIL — `ImportError: cannot import name 'resolve_join_tenant'`.

- [ ] **Step 3: Implement the helper**

Append to `tenants/services.py` (add `from django.conf import settings` to the top-level imports if absent):

```python
def resolve_join_tenant(slug: str | None) -> Tenant | None:
  """Tenant targeted by the public join flow (family home, join request).

  With multi-tenancy on, ``slug`` selects the tenant. Without multi-tenancy
  only the default tenant exists: ``None`` (the legacy alias) and the default
  slug resolve to it, any other slug is refused. Returns ``None`` when no
  active tenant matches — callers raise 404.
  """
  default = Tenant.get_default()
  if slug is None:
    return default
  tenant = Tenant.objects.filter(slug=slug).first()
  if tenant is None or not tenant.is_active:
    return None
  if not settings.MULTI_TENANT_ENABLED and tenant.pk != default.pk:
    return None
  return tenant
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `make test t=tenants.tests.tests_join_flow`
Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tenants/services.py tenants/tests/tests_join_flow.py
git commit -m "feat(tenants): resolve_join_tenant helper for the public join flow"
```

---

### Task 2: `TenantHomeView` + `tenant-home` route

**Files:**
- Create: `tenants/views/views_home.py`
- Modify: `cousinsmatter/urls.py` (imports at top; routes appended after the `tenants/` include line, before the `static(...)` lines)
- Test: `tenants/tests/tests_join_flow.py` (extend)

**Interfaces:**
- Consumes: `resolve_join_tenant` (Task 1), `tenant_context` (`tenants/scoping.py`), `LoginView` (django.contrib.auth).
- Produces: route `tenant-home` = `/<slug:slug>/`, class `TenantHomeView`. Task 3 redirects to it (`redirect("tenant-home", slug=...)`); Task 4 links to it.

- [ ] **Step 1: Write failing tests**

Append to `tenants/tests/tests_join_flow.py`:

```python
@override_settings(MULTI_TENANT_ENABLED=True)
class TenantHomeTests(MemberTestCase):
  def setUp(self):
    super().setUp()
    self.tenant = Tenant.objects.create(name="Famille Dubois", slug="famille-dubois")
    TenantSettings.objects.create(tenant=self.tenant, overrides={"SITE_NAME": "Famille Dubois"})

  def test_home_renders_login_page_with_family_branding(self):
    response = self.client.get(reverse("tenant-home", args=["famille-dubois"]))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "members/login/login.html")
    self.assertContains(response, "Famille Dubois")

  def test_home_login_post_works(self):
    response = self.client.post(
      reverse("tenant-home", args=["famille-dubois"]),
      {"username": self.superuser.username, "password": self.superuser.password},
      follow=True,
    )
    self.assertTrue(response.context["user"].is_authenticated)

  def test_unknown_slug_404(self):
    response = self.client.get(reverse("tenant-home", args=["inconnu"]))
    self.assertEqual(response.status_code, 404)

  def test_inactive_tenant_404(self):
    self.tenant.is_active = False
    self.tenant.save()
    response = self.client.get(reverse("tenant-home", args=["famille-dubois"]))
    self.assertEqual(response.status_code, 404)


@override_settings(MULTI_TENANT_ENABLED=False)
class TenantHomeFlagOffTests(MemberTestCase):
  def test_default_tenant_home_works(self):
    response = self.client.get(reverse("tenant-home", args=[Tenant.get_default().slug]))
    self.assertEqual(response.status_code, 200)

  def test_other_tenant_slug_404(self):
    tenant = Tenant.objects.create(name="Other", slug="other")
    response = self.client.get(reverse("tenant-home", args=[tenant.slug]))
    self.assertEqual(response.status_code, 404)
```

Also add `from django.urls import reverse` to the file's imports (not yet present after Task 1 edit — keep only imports actually used, ruff will tell you).

- [ ] **Step 2: Run tests to verify they fail**

Run: `make test t=tenants.tests.tests_join_flow`
Expected: new tests FAIL with 404/`NoReverseMatch` (view and route do not exist).

- [ ] **Step 3: Implement the view**

Create `tenants/views/views_home.py`:

```python
"""Tenant-scoped anonymous home: the pre-tenancy unauthenticated page."""

from django.contrib.auth.views import LoginView
from django.http import Http404
from django.views import generic

from core.mixins import LoginNotRequiredMixin

from ..scoping import tenant_context
from ..services import resolve_join_tenant

# Same view class as members:login, so the family home behaves exactly like
# the global one (login form, language, password reset) — only branding differs.
login_view = LoginView.as_view(template_name="members/login/login.html")


class TenantHomeView(LoginNotRequiredMixin, generic.View):
  def get(self, request, slug):
    return self._scoped(request, slug)

  def post(self, request, slug):
    return self._scoped(request, slug)

  def _scoped(self, request, slug):
    tenant = resolve_join_tenant(slug)
    if tenant is None:
      raise Http404
    request.tenant = tenant
    with tenant_context(tenant):
      return login_view(request)
```

- [ ] **Step 4: Wire the route**

In `cousinsmatter/urls.py`, add to the top imports:

```python
from members.views import views_registration
from tenants.views import views_home
```

Then, immediately after the line

```python
+([path("tenants/", include("tenants.urls"))] if settings.MULTI_TENANT_ENABLED else [])
```

insert (before the `+ static(...)` lines):

```python
# Tenant-scoped anonymous surfaces (family home + join request). Always
# mounted: without multi-tenancy the views resolve the default tenant.
# Kept last — tenant-home is a catch-all.
+[
  path(
    "<slug:slug>/join/",
    views_registration.TenantJoinRequestView.as_view(),
    name="tenant-join",
  ),
  path("<slug:slug>/", views_home.TenantHomeView.as_view(), name="tenant-home"),
]
```

Note: `views_registration.TenantJoinRequestView` does not exist until Task 3 — to keep this task green, temporarily route `tenant-join` to `views_home.TenantHomeView.as_view()` and swap it in Task 3 Step 4. The `tenant-home` tests must pass now.

- [ ] **Step 5: Run tests to verify they pass**

Run: `make test t=tenants.tests.tests_join_flow`
Expected: all PASS (6 + 6).

- [ ] **Step 6: Commit**

```bash
git add tenants/views/views_home.py cousinsmatter/urls.py tenants/tests/tests_join_flow.py
git commit -m "feat(tenants): tenant-scoped anonymous home at /<slug>/"
```

---

### Task 3: `TenantJoinRequestView` replaces `RegistrationRequestView`

**Files:**
- Modify: `members/views/views_registration.py` (replace class `RegistrationRequestView`, lines 220-283; add imports)
- Modify: `members/urls.py:67` (swap view class on the `register/request` route)
- Modify: `cousinsmatter/urls.py` (point `tenant-join` at the real view — undo Task 2's temporary wiring)
- Test: `members/tests/tests_register.py` (extend)

**Interfaces:**
- Consumes: `resolve_join_tenant` (Task 1), `admin_or_superusers` (`tenants/authz.py:46`, returns list[Member]), `tenant_context`, `tenant_setting`.
- Produces: `TenantJoinRequestView` (GET/POST, `slug=None` for the alias). Existing `members:register_request` name and URL unchanged.

- [ ] **Step 1: Write failing tests**

Add to `members/tests/tests_register.py` imports:

```python
from django.core.cache import cache
from django.test import override_settings

from tenants.models import Tenant
```

Append at the end of the file:

```python
@override_settings(MULTI_TENANT_ENABLED=True)
class TenantJoinRequestTests(RequestRegistrationLinkTests):
  def setUp(self):
    super().setUp()
    cache.clear()
    self.tenant = Tenant.objects.create(name="Famille Dupont", slug="famille-dupont")
    self.tenant_admin = Member.unscoped.create(
      username="dupont-admin",
      email="admin@dupont.fr",
      tenant=self.tenant,
      role=Member.Role.ADMIN,
      is_active=True,
    )

  @staticmethod
  def join_data(email="new@cousin.fr"):
    return {
      "name": "New Cousin",
      "email": email,
      "message": "Hello!",
      "captcha_0": "whatever",
      "captcha_1": "passed",
    }

  @ignore_captcha_errors()
  def test_join_request_emails_tenant_admins_not_superusers(self):
    response = self.client.post(reverse("tenant-join", args=["famille-dupont"]), self.join_data(), follow=True)
    self.assertEqual(len(mail.outbox), 1)
    self.assertSequenceEqual(mail.outbox[0].recipients(), [self.tenant_admin.email])
    self.assertNotIn(self.superuser.email, mail.outbox[0].recipients())
    self.assertContainsMessage(response, "success", _("Registration request sent."))

  @ignore_captcha_errors()
  def test_join_request_redirects_to_family_home(self):
    response = self.client.post(reverse("tenant-join", args=["famille-dupont"]), self.join_data())
    self.assertRedirects(response, reverse("tenant-home", args=["famille-dupont"]))

  @ignore_captcha_errors()
  def test_join_request_unknown_slug_404(self):
    response = self.client.post(reverse("tenant-join", args=["inconnu"]), self.join_data())
    self.assertEqual(response.status_code, 404)

  @ignore_captcha_errors()
  def test_join_request_existing_email_rejected_unscoped(self):
    data = self.join_data(email=self.superuser.email)  # member of ANOTHER tenant
    response = self.client.post(reverse("tenant-join", args=["famille-dupont"]), data, follow=True)
    self.assertContainsMessage(response, "danger", _("A member with this email already exists."))
    self.assertEqual(len(mail.outbox), 0)

  @ignore_captcha_errors()
  def test_join_request_throttled_after_five_posts(self):
    for i in range(5):
      self.client.post(
        reverse("tenant-join", args=["famille-dupont"]),
        self.join_data(email=f"cousin{i}@cousin.fr"),
      )
    response = self.client.post(
      reverse("tenant-join", args=["famille-dupont"]),
      self.join_data(email="sixth@cousin.fr"),
      follow=True,
    )
    self.assertContainsMessage(response, "danger", _("Too many requests, please try again later."))
    self.assertEqual(len(mail.outbox), 5)


class JoinFlagOffTests(MemberTestCase):
  @override_settings(MULTI_TENANT_ENABLED=False)
  def test_join_non_default_slug_404(self):
    tenant = Tenant.objects.create(name="Other", slug="other")
    response = self.client.get(reverse("tenant-join", args=[tenant.slug]))
    self.assertEqual(response.status_code, 404)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `make test t=members.tests.tests_register`
Expected: new tests FAIL (`NoReverseMatch` or 404 on `tenant-join`); the pre-existing `RequestRegistrationLinkTests` still PASS (legacy URL untouched so far).

- [ ] **Step 3: Implement the view**

In `members/views/views_registration.py`, add to imports:

```python
from django.core.cache import cache
from django.http import Http404

from tenants.services import resolve_join_tenant
```

Delete the whole `RegistrationRequestView` class (lines 220-283) and put in its place:

```python
class TenantJoinRequestView(LoginNotRequiredMixin, generic.View):
  """Anonymous request to join a family (captcha; routed to its admins).

  The tenant comes from the URL slug; the legacy ``members:register_request``
  alias and flag-off deployments resolve to the default tenant. The request is
  emailed to the tenant's admins (fallback: platform superusers) with a
  prefilled invitation link.
  """

  template_name = "members/registration/registration_request.html"

  THROTTLE_LIMIT = 5  # submissions per hour per IP, same policy as other
  THROTTLE_SECONDS = 3600  # anonymous public forms

  def get(self, request, slug=None):
    tenant = resolve_join_tenant(slug)
    if tenant is None:
      raise Http404
    request.tenant = tenant
    with tenant_context(tenant):
      return render(request, self.template_name, {"form": RegistrationRequestForm()})

  def post(self, request, slug=None):
    tenant = resolve_join_tenant(slug)
    if tenant is None:
      raise Http404
    request.tenant = tenant
    with tenant_context(tenant):
      form = RegistrationRequestForm(request.POST)
      if form.is_valid():
        if self._throttled(request):
          messages.error(request, _("Too many requests, please try again later."))
          return render(request, self.template_name, {"form": form})
        email = form.cleaned_data["email"]
        if Member.unscoped.filter(email=email).exists():
          # email login is global: an existing member can never re-claim it here
          messages.error(request, _("A member with this email already exists."))
          return render(request, self.template_name, {"form": form})
        if self._send_request(tenant, form.cleaned_data, request):
          messages.success(request, _("Registration request sent."))
          return redirect("tenant-home", slug=tenant.slug)
        messages.error(request, _("Unable to send mail, please contact your administrator"))
      return render(request, self.template_name, {"form": form})

  def _send_request(self, tenant, data, request) -> bool:
    """Render + send the request email to the tenant's admins. True on success."""
    site_name = tenant_setting("site_name")
    msg = render_to_string(
      "members/email/registration_request_email.html",
      {
        "site_name": site_name,
        "requester": {"email": data["email"], "name": data["name"], "message": data["message"]},
        "link": request.build_absolute_uri(reverse("members:invite")),
      },
      request=request,
    )
    admins = admin_or_superusers(tenant)
    if not admins:
      return False
    return (
      send_mail(
        _("Registration request for %(site_name)s") % {"site_name": site_name},
        strip_tags(msg),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[admin.email for admin in admins],
        html_message=msg,
      )
      == 1
    )

  def _throttled(self, request) -> bool:
    key = f"join-request:{request.META.get('REMOTE_ADDR', 'unknown')}"
    count = cache.get_or_set(key, 0, self.THROTTLE_SECONDS)
    if count >= self.THROTTLE_LIMIT:
      return True
    try:
      cache.incr(key)
    except ValueError:
      cache.set(key, 1, self.THROTTLE_SECONDS)
    return False
```

Notes: the email template `members/email/registration_request_email.html` is **not modified** — it already renders `site_name` (now the family's, via tenant context), the requester info and the prefilled `?mail=` link. `tenant_setting("site_name")` resolves inside the active `tenant_context`.

- [ ] **Step 4: Wire the routes**

In `members/urls.py`, change the `register/request` route's view class:

```python
(
  path(
    "register/request",
    views_registration.TenantJoinRequestView.as_view(),
    name="register_request",
  ),
)
```

In `cousinsmatter/urls.py`, replace the temporary `tenant-join` target from Task 2 with:

```python
(views_registration.TenantJoinRequestView.as_view(),)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `make test t=members.tests.tests_register && make test t=tenants.tests.tests_join_flow`
Expected: ALL PASS — including the pre-existing `RequestRegistrationLinkTests` (flag-off regression; with a single superuser, recipients `[superuser.email]` is unchanged).

- [ ] **Step 6: Commit**

```bash
git add members/views/views_registration.py members/urls.py cousinsmatter/urls.py members/tests/tests_register.py
git commit -m "feat(members): join request routed to the tenant's admins

RegistrationRequestView becomes TenantJoinRequestView: tenant from the
URL slug (default tenant for the legacy alias), email to
admin_or_superusers(tenant), IP throttle, unscoped duplicate check."
```

---

### Task 4: Templates — contextual links, family name, shareable home URL

**Files:**
- Modify: `members/templates/members/login/login.html:16-25`
- Modify: `core/templates/core/unauthenticated-navbar.html:55-58`
- Modify: `members/templates/members/registration/registration_request.html:8-10`
- Modify: `members/templates/members/registration/registration_invite.html` (before closing `</div>` of the container)
- Modify: `members/views/views_registration.py` (`MemberInvitationView.get` and `.post` contexts)
- Test: `tenants/tests/tests_join_flow.py` + `members/tests/tests_register.py` (extend)

**Interfaces:**
- Consumes: `settings.MULTI_TENANT_ENABLED` (already in `EXPOSED_SETTINGS`, `core/context_processors.py:11`), `request.tenant` set by the middleware (None) and by the new views (tenant).
- Produces: `join_url` context variable in `MemberInvitationView` (GET and POST).

- [ ] **Step 1: Write failing tests**

Append to `tenants/tests/tests_join_flow.py` inside `TenantHomeTests`:

```python
  def test_join_link_visible_on_family_home_only(self):
    family = self.client.get(reverse("tenant-home", args=["famille-dubois"]))
    self.assertContains(family, reverse("tenant-join", args=["famille-dubois"]))
    global_login = self.client.get(reverse("members:login"))
    self.assertNotContains(global_login, reverse("tenant-join", args=["famille-dubois"]))
```

Append to `members/tests/tests_register.py` inside `JoinFlagOffTests`:

```python
  def test_legacy_link_visible_when_flag_off(self):
    response = self.client.get(reverse("members:login"))
    self.assertContains(response, reverse("members:register_request"))
```

And in `TenantJoinRequestTests`:

```python
  def test_invite_page_shows_family_home_url(self):
    self.client.login(username=self.superuser.username, password=self.superuser.password)
    response = self.client.get(reverse("members:invite"))
    self.assertContains(response, reverse("tenant-home", args=[self.superuser.tenant.slug]))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `make test t=members.tests.tests_register && make test t=tenants.tests.tests_join_flow`
Expected: the 3 new tests FAIL (links not contextual yet, `join_url` missing → template renders empty href).

- [ ] **Step 3: Edit the templates**

`members/templates/members/login/login.html` — replace the "Need An Account?" block (lines 16-25) with:

```html
<div class="container is-small">
  {% translate "Need An Account?" %}
  {% if request.tenant %}
  <a class="is-2" href="{% url 'tenant-join' request.tenant.slug %}">{% translate "Request invitation link" %}</a>
  {% elif not settings.MULTI_TENANT_ENABLED %}
  <a class="is-2" href="{% url 'members:register_request' %}">{% translate "Request invitation link" %}</a>
  {% endif %}
  {% if settings.SAAS_LANDING_ENABLED %}
  {% translate "or" %}
  <a class="is-2" href="{% url 'saas:signup' %}">{% translate "Create new family" %}</a>
  {% elif settings.MULTI_TENANT_ENABLED %}
  {% translate "or" %}
  <a class="is-2" href="{% url 'tenants:family_signup' %}">{% translate "Create new family" %}</a>
  {% endif %}
</div>
```

`core/templates/core/unauthenticated-navbar.html` — replace lines 55-58 with:

```html
					{% if request.tenant %}
					<a class="button has-background-link-light has-text-link" href="{% url 'tenant-join' request.tenant.slug %}">
						{%icon "invite-request" %}
						<span><strong>{%trans "Request invitation link" %}</strong></span>
					</a>
					{% elif not settings.MULTI_TENANT_ENABLED %}
					<a class="button has-background-link-light has-text-link" href="{% url 'members:register_request' %}">
						{%icon "invite-request" %}
						<span><strong>{%trans "Request invitation link" %}</strong></span>
					</a>
					{% endif %}
```

`members/templates/members/registration/registration_request.html` — replace lines 8-10 with:

```html
	<p class="content">
		{% blocktranslate with name=settings.SITE_NAME %}By completing and submitting this form, you are asking the administrators of the "{{ name }}" family site to send you an invitation link.{% endblocktranslate %}
	</p>
```

`members/templates/members/registration/registration_invite.html` — just before the container's closing `</div>` (after the form, line 13):

```html
	<p class="content has-text-centered">
		{% blocktranslate with url=join_url %}To let relatives request their invitation themselves, share your family home page: <a href="{{ url }}">{{ url }}</a>{% endblocktranslate %}
	</p>
```

- [ ] **Step 4: Add `join_url` to the invitation view**

In `members/views/views_registration.py`, in `MemberInvitationView.post`, inside the `form.is_valid()` branch (after `from_email = ...`), and in `MemberInvitationView.get` before the `return render(...)`, add:

```python
    join_url = request.build_absolute_uri(reverse("tenant-home", args=[request.user.tenant.slug]))
```

and add `"join_url": join_url,` to **every** `render(request, self.template_name, {...})` context dict of `MemberInvitationView` — `post` renders three times (form invalid, email already exists, success) and `get` once.

- [ ] **Step 5: Run tests to verify they pass**

Run: `make test t=members.tests.tests_register && make test t=tenants.tests.tests_join_flow`
Expected: ALL PASS.

- [ ] **Step 6: Commit**

```bash
git add members/templates/members/login/login.html core/templates/core/unauthenticated-navbar.html members/templates/members/registration/registration_request.html members/templates/members/registration/registration_invite.html members/views/views_registration.py members/tests/tests_register.py tenants/tests/tests_join_flow.py
git commit -m "feat(ui): contextual invitation-request links and family-scoped copy"
```

---

### Task 5: Extend `RESERVED_TENANT_SLUGS`

**Files:**
- Modify: `tenants/forms.py:13-21` (the `RESERVED_TENANT_SLUGS` frozenset)
- Test: `tenants/tests/tests_join_flow.py` (extend)

**Interfaces:**
- Consumes: existing `uniquify_tenant_slug` guard (`tenants/forms.py:33`).
- Produces: nothing new — validation only.

- [ ] **Step 1: Write failing test**

Append to `tenants/tests/tests_join_flow.py`:

```python
class ReservedSlugTests(MemberTestCase):
  def test_reserved_slug_rejected(self):
    from django.forms import ValidationError

    from ..forms import uniquify_tenant_slug

    for name in ("Members", "Accounts", "Chat & Galleries"):
      with self.assertRaises(ValidationError):
        uniquify_tenant_slug(name)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `make test t=tenants.tests.tests_join_flow`
Expected: FAIL — `members`/`accounts` are not reserved yet (`chat` already is).

- [ ] **Step 3: Extend the frozenset**

Replace `RESERVED_TENANT_SLUGS` in `tenants/forms.py` with:

```python
# Slugs a family may never take: seeded/special tenants, plus the first
# segment of every root route and the media/static prefixes — a tenant slug
# would otherwise shadow them in the tenant-home catch-all.
RESERVED_TENANT_SLUGS = frozenset({
  settings.DEFAULT_TENANT_SLUG,
  settings.SYSTEM_TENANT_SLUG,
  "admin",
  "admins",
  "manage",
  "settings",
  "signup",
  "accounts",
  "members",
  "posts",
  "chat",
  "galleries",
  "polls",
  "genealogy",
  "password",
  "captcha",
  "i18n",
  "health",
  "qhealth",
  "tenants",
  "saas",
  "troves",
  "classified-ads",
  "pages-edit",
  "robots.txt",
  "static",
  "media",
  "protected-media",
})
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `make test t=tenants.tests.tests_join_flow`
Expected: ALL PASS.

- [ ] **Step 5: Commit**

```bash
git add tenants/forms.py tenants/tests/tests_join_flow.py
git commit -m "feat(tenants): reserve root route first segments from tenant slugs"
```

---

### Task 6: Translations, docs fiches, full verification

**Files:**
- Modify: `members/locale/*/LC_MESSAGES/django.po` (via make), `docs/apps/members.md`, `docs/apps/tenants.md`
- Test: full suite

**Interfaces:**
- Consumes: all previous tasks.
- Produces: compiled translations; up-to-date OKF fiches.

- [ ] **Step 1: Update translation catalogs**

Run: `make mkmsg a=members`
Fill the new `msgstr` in `members/locale/fr/LC_MESSAGES/django.po`:

```po
msgid "Too many requests, please try again later."
msgstr "Trop de demandes, veuillez réessayer plus tard."

msgid ""
By completing and submitting this form, you are asking the administrators of "
"the \"{{ name }}\" family site to send you an invitation link."
msgstr ""
"En remplissant et en envoyant ce formulaire, vous demandez aux "
"administrateurs du site de la famille « {{ name }} » de vous envoyer un lien "
"d'invitation."

msgid ""
To let relatives request their invitation themselves, share your family home "
"page: <a href=\"{{ url }}\">{{ url }}</a>"
msgstr ""
"Pour permettre à vos proches de demander leur invitation, partagez la page "
"d'accueil de votre famille : <a href=\"{{ url }}\">{{ url }}</a>"
```

(Use the exact `msgid` blocks generated by `mkmsg`; leave the other locales untranslated — they fall back to English.)

Run: `make cpmsg a=members`

- [ ] **Step 2: Update the OKF fiches**

`docs/apps/members.md` — add a short section:

```markdown
## Join request (tenant-scoped)

Anonymous visitors request an invitation from a family page: `/<slug>/join/`
(`tenant-join`) emails the family's admins (`admin_or_superusers`) with a
prefilled invitation link. `/members/register/request` (`members:register_request`)
is an alias resolving to the default tenant; with `MULTI_TENANT_ENABLED=False`
it is the only entry point and behaves as before. The global link is shown on
unscoped pages only when multi-tenancy is off.
```

`docs/apps/tenants.md` — add:

```markdown
## Family home (anonymous)

`/<slug>/` (`tenant-home`, `tenants.views.views_home.TenantHomeView`) renders
the family's unauthenticated page: the same LoginView as `members:login`,
branded by the tenant (`request.tenant`). Without multi-tenancy only the
default tenant's slug responds; other slugs 404. Tenant slugs cannot shadow
root routes (`RESERVED_TENANT_SLUGS`).
```

Then bump each fiche's `stale_after` date to today and run:

Run: `make check-docs`
Expected: PASS (no stale fiches reported).

- [ ] **Step 3: Full verification**

Run:
```bash
make check
make test
make test-ui t=members.tests.ui.tests_ui_forms
```
Expected: `make check` clean; full test suite PASS; the UI form tests (which open `members:register_request`) PASS unchanged.

Manual smoke check (flag off and on): `make run`, then visit
`http://localhost:8000/<default-slug>/` (login page, family-branded),
`http://localhost:8000/members/register/request` (form), and with
`MULTI_TENANT_ENABLED=True` a non-default family's `/<slug>/` and `/<slug>/join/`.

- [ ] **Step 4: Commit**

```bash
git add members/locale docs/apps/members.md docs/apps/tenants.md
git commit -m "chore: translations and docs fiches for the tenant join flow"
```

---

## Verification (end-to-end)

1. Flag off (default): `/members/register/request` works exactly as before; login page shows the legacy link; `/<other-slug>/` → 404.
2. Flag on: `/<slug>/` renders the family-branded login page; its "Request invitation link" goes to `/<slug>/join/`; submitting emails the family's admins (not the superuser); the admin opens the prefilled `members:invite` from the email and invites the requester; the requester registers through the signed tenant-bound link.
3. Global pages with flag on (`/accounts/login/`) show no invitation-request link.
