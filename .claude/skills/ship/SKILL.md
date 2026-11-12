---
description: Verify then commit and push
---
1. Run `make check` (ruff + pyright)
2. Run unit tests (`make test`) and, if UI files changed, the Playwright UI suite (`make test-ui`, 190 tests)
3. If the change touches multi-tenant behavior (tenants app, tenant-scoped querysets, auth middleware — anything affecting authenticated users), also run `make test-mt` on the touched modules before the PR: CI runs the suite with `MULTI_TENANT_ENABLED=True`, and feature-gated modules (e.g. `tenants/tests/tests_feature_on.py`) are **skipped** in a plain local run, so a green `make test` alone does not prove CI green
4. If all green: `git add -A`, commit with a descriptive message, `git push origin HEAD`
5. Report commit hash and test summary
