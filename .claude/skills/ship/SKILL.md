---
description: Verify then commit and push
---
1. Run `make check` (ruff + pyright)
2. Run unit tests (`make test`) and, if UI files changed, the Playwright suite (`make test-ui`)
3. If all green: `git add -A`, commit with a descriptive message, `git push origin HEAD`
4. Report commit hash and test summary
