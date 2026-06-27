---
description: Creates Playwright-based UI tests for Django apps that don't have them yet. Use when the user asks to "create UI tests", "add Playwright tests", "write UI tests for [app]", "écrire des tests UI", or mentions testing user interfaces with Playwright
---

# Skill: Create Playwright UI Tests for cousins-matter

You are a specialized assistant for creating UI tests in the `cousins-matter` Django project. This project uses **Playwright** via a custom base class `PlaywrightTestCase`. Follow the project's existing conventions scrupulously.

---

## Step 0 - Verify Playwright is installed

Always check first that the `playwright` module is available in the project's virtual environment:

```bash
source .venv/bin/activate && python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

If Playwright is not installed, the `PlaywrightTestCase` class is disabled via `@unittest.skipUnless` and tests will be silently skipped. Ask the user to install it with `uv add playwright` followed by `playwright install chromium` before continuing.

---

## Step 1 - Analyze the target app

Before writing any test, explore the target app to understand WHAT to test:

1. **Read the models**: `{app}/models.py` — understand the entities and their relationships, field choices, constraints.
2. **Read the URLs**: `{app}/urls.py` — identify all routes and their names (e.g., `forum:list`, `forum:create`).
3. **Read the views**: `{app}/views*.py` or `{app}/views/*.py` — understand permissions, context data, forms used.
4. **Read the templates**: `{app}/templates/{app}/*.html` or `{app}/templates/{app}/**/*.html` — identify relevant CSS selectors:
   - Titles: `h1.title`, `.title`, `.subtitle`
   - Containers: `.container`, `.panel`, `.card`, `.box`, `.cell`
   - Forms: `form`, `input[name='...']`, `select[name='...']`, `textarea[name='...']`
   - Buttons: `button[type='submit']`, `a.button`, `.buttons`
   - Lists: `.cell` (grid), `tr` (table), `.panel-block`
   - Navigation: `nav.navbar`, `footer.footer`
   - Pagination: `a.pagination-link`
   - HTMX elements: `[hx-get]`, `[hx-post]`, `[hx-target]`, `[hx-trigger]`, `[hx-confirm]`
   - CSRF: `input[name='csrfmiddlewaretoken']`

5. **Check existing factories**: `{app}/tests/factories.py`. All apps in this project already have factories. If a factory has expensive `@post_generation` hooks (e.g., `FamilyFactory` generates a 10-generation tree, `ChatRoomFactory` creates 5-15 messages), pass flags like `create_messages=False` or `create_children=False` in UI tests to keep them fast.

---

## Step 2 - Determine the test structure

There are two patterns in the project, based on app complexity:

### Pattern A - Simple app (like `core`)

The app does not need complex fixtures. Tests extend `PlaywrightTestCase` directly.

File structure:
```
{app}/tests/ui/
  __init__.py    -> empty (0-byte file)
  tests_ui_X.py  -> imports PlaywrightTestCase from core.tests.ui
```

Each test file starts with:
```python
from core.tests.ui import PlaywrightTestCase
```

### Pattern B - Complex app (like `galleries`, `troves`)

The app needs fixtures (objects created via factories) before each test. Create a local `base.py`.

File structure:
```
{app}/tests/ui/
  __init__.py    -> empty (0-byte file)
  base.py        -> extends PlaywrightTestCase, creates test data in setUp()
  tests_ui_X.py  -> imports from .base
```

`base.py` template:
```python
from core.tests.ui import PlaywrightTestCase
from {app}.tests.factories import XxxFactory, YyyFactory


class {App}UITestBase(PlaywrightTestCase):
    """Base class for {App} UI tests with pre-created test fixtures."""

    def setUp(self):
        super().setUp()
        # self.user is already created by PlaywrightTestCase.setUp()

        # Create test objects via factories
        self.obj1 = XxxFactory(...)
        self.obj2 = YyyFactory(...)
```

**Decision rule**: Use Pattern B if and only if the tests need objects created via factories beyond just the admin user. Pattern B is needed for: `members`, `chat`, `forum`, `polls`, `classified_ads`, `genealogy`. Pattern A is sufficient for: `pages` (admin-only, simple CRUD).

**Important for Pattern B**: The `setUp` method should NOT re-create `self.errors` and the `pageerror` listener. The parent `PlaywrightTestCase.setUp()` does this too, and is called in the setup. Do NOT re-create the user — `self.user` is already created by `PlaywrightTestCase.setUp()`, and re-creating it causes a duplicate key error.

---

## Step 3 - Create the directory structure

```bash
mkdir -p {app}/tests/ui/
```

Create `{app}/tests/ui/__init__.py` — an **empty file** (0 bytes). This exists solely to make `ui` a Python package. Do NOT add any imports to it (unlike `core/tests/ui/__init__.py` which exports `PlaywrightTestCase`).

If using Pattern B, also create `{app}/tests/ui/base.py`.

---

## Step 4 - Write the tests

Organize tests by feature/logic in separate files (following `core`'s pattern: `tests_ui_home.py`, `tests_ui_about.py`, `tests_ui_contact.py`). Group related tests together.

### Naming conventions

- Files: `tests_ui_{feature}.py` (e.g., `tests_ui_members.py`, `tests_ui_profile.py`)
- Classes: `{Feature}UITest` (e.g., `MembersListUITest`, `ForumPostUITest`)
- Methods: `test_{action}_{context}` (e.g., `test_members_list_requires_auth`, `test_members_list_display`)

### Standard test patterns

Don't add assertion on No JS errors at the end of each test execpt case D, this is already done by PlaywrightTestCase.teardown().

#### A. Authentication required test

```python
def test_members_page_requires_auth(self):
  """The members page should redirect to login when not authenticated."""
  self.goto_page("members:members")
  self.assert_url_contains("/login/", "Unauthenticated user should be redirected to login")
```

#### B. Page display test

```python
def test_members_list_display(self):
  """The members list should display the title and members for authenticated users."""
  self.login_and_goto_page("members:members")

  # Title visible
  self.assert_visible("h1.title", "Page title should be visible")

  # Content present
  cells = self.page.locator(".cell")
  self.assertGreaterEqual(cells.count(), 1, "At least one member should be displayed")
```

#### C. Form display test

If the form has no id, create one in the template and use it for the CSRF token check, otherwise the test will complain of several tokens. In some cases, the used CSRF is the one on the html body, not in the form.

```python
def test_create_post_form_display(self):
  """The create post form should display all expected fields."""
  self.login_and_goto_page("forum:create")

  # Title
  self.assert_visible("h1.title", "Form title should be visible")

  # Form fields
  self.assert_visible("input[name='title']", "Title input should be visible")
  self.assert_visible("textarea[name='content']", "Content textarea should be visible")

  # Buttons
  self.assert_visible("button[type='submit']", "Submit button should be visible")

  # if CSRF token on the form
  self.assert_hidden("form#contact_form input[name='csrfmiddlewaretoken']", "CSRF token should be present")
```

#### D. No JS errors test

```python
def test_members_list_no_js_errors(self):
  """The members list should not produce JavaScript errors."""
  self.login_and_goto_page("members:members")
  self.page.wait_for_timeout(1000)
  self.assertEqual(len(self.errors), 0, f"JS errors: {self.errors}")
```

#### E. Navigation test

```python
def test_navigate_to_member_detail(self):
  """Clicking a member in the list should navigate to their detail page."""
  # Go to list
  self.login_and_goto_page("members:members")
  self.page.wait_for_selector(".cell")

  # Click first member link
  first_member_link = self.page.locator(".cell a").first
  first_member_link.click()
  self.page.wait_for_timeout(500)

  # Verify we're on a detail page
  self.assertIn("/members/", self.page.url)
  self.assert_visible(".card", "Member detail card should be visible")
```

#### F. HTMX interaction test

```python
def test_delete_via_htmx(self):
  """The HTMX delete button should remove the element from the DOM."""
  obj = self.my_objects[0]
  self.login_and_goto_page("app:list")
  self.page.wait_for_selector(f"#item-{obj.id}")

  # Handle hx-confirm dialog
  self.page.on("dialog", lambda dialog: dialog.accept())

  # Click the HTMX delete button
  delete_button = self.page.locator(f"#item-{obj.id} [hx-delete]")
  self.assertTrue(delete_button.is_visible(), "Delete button should be visible")
  delete_button.click()

  # Element should be removed from DOM
  self.page.wait_for_selector(f"#item-{obj.id}", state="detached", timeout=3000)
  self.assertTrue(
    self.page.locator(f"#item-{obj.id}").count() == 0,
    "Deleted element should no longer be in the DOM",
  )
```

#### G. Dropdown / filter test

```python
def test_filter_by_category(self):
  """The category dropdown should filter items."""
  self.login_and_goto_page("app:list")
  self.page.wait_for_selector(".cell")

  # Select a category
  dropdown = self.page.locator('select[name="category"]')
  dropdown.select_option("my-category")
  self.page.wait_for_timeout(500)

  # Verify filtering happened
  cells = self.page.locator(".cell")
  self.assertGreaterEqual(cells.count(), 0, "Filtered results should be shown")
```

---

## Step 5 - Verification checklist

For each test file produced, verify:

1. [ ] Imports are correct: the appropriate base class import.
2. [ ] `self.goto_page("namespace:name")` precedes every access to a page not requiring authentication.
3. [ ] `self.login_and_goto_page("namespace:name")` precedes every access to a page requiring authentication.
4. [ ] CSS selectors match exactly what is in the templates.
5. [ ] Factory field values match the model's `choices` definitions (verify with `{app}/models.py`).

---

## Step 6 - Run the tests

Once written, run them with:

```bash
source .venv/bin/activate

# Run a specific test class
make test-ui t=<app>.tests.ui.<module>.<TestClass>

# Run a specific test method
make test-ui t=<app>.tests.ui.<module>.<TestClass>.<test_method>

# With --keepdb for faster repeated runs
make test-ui o="--keepdb" t=<app>.tests.ui.<module>.<TestClass>
```

Examples:
```bash
make test-ui t=members.tests.ui.tests_ui_members.MembersListUITest
make test-ui t=forum.tests.ui.tests_ui_posts.ForumPostUITest.test_post_list_display
make test-ui o="--keepdb" t=chat.tests.ui.tests_ui_rooms.ChatRoomsUITest
```

---

## Key reference files

- **PlaywrightTestCase base class**: `core/tests/ui/test_ui_base.py`
  - Provides helpers: `url()`, `login()`, `assert_visible()`, `assert_hidden()`, `assert_url_contains()`, `take_screenshot()`
  - Creates an admin superuser (`admin`/`password`) in `setUp`
  - Initializes `self.errors` list with `pageerror` listener in `setUp`
  - Configures browser lifecycle at class level (one browser for all tests in a class)
  - Decorated with `@tag("ui")` and `@unittest.skipUnless(PLAYWRIGHT_AVAILABLE, ...)`
  - Uses `fixtures = ["predefined_flatpages.json"]` to avoid flatpage-related errors
- **PlaywrightTestCase export**: `core/tests/ui/__init__.py`
  - Entry point: `from core.tests.ui import PlaywrightTestCase`
- **Pattern A example (simple)**: `core/tests/ui/tests_ui_home.py`, `core/tests/ui/tests_ui_about.py`, `core/tests/ui/tests_ui_contact.py`
- **Pattern B example (complex)**: `galleries/tests/ui/base.py`, `galleries/tests/ui/tests_ui_gallery.py`, `galleries/tests/ui/tests_ui_slideshow.py`
- **Pattern B with mocks**: `troves/tests/ui/base.py`, `troves/tests/ui/tests_ui_troves.py`
- **Existing factories**: `{app}/tests/factories.py` for each app, plus `members/tests/factories.py` (MemberFactory, FamilyFactory, AddressFactory)
- **Makefile**: `test-ui` target at project root

---

## Important reminders

1. **`__init__.py` files in `{app}/tests/ui/` are empty (0 bytes)**. Do not add imports. Import `Playwrigh