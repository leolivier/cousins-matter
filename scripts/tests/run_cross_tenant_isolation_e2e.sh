#!/usr/bin/env bash
# Automated version of docs/flows/cross-tenant-isolation.md.
#
# Runs the isolation scenario phases in order (test_01 .. test_08) with
# MULTI_TENANT_ENABLED=True, as CI does. Requires PostgreSQL (make up4run) and
# an .env with the DB credentials.
#
# Usage: scripts/tests/run_cross_tenant_isolation_e2e.sh [extra make test options]
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 1

if make test-mt t=members.tests.tests_cross_tenant_isolation_e2e o="-v 2 --noinput"; then
  echo "cross-tenant isolation E2E: all phases passed"
else
  echo "cross-tenant isolation E2E: FAILED" >&2
  exit 1
fi
