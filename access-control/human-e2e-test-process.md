# Human E2E Test Process

Status: Draft
Phase: Phase 6 - Production MVP
Scope: Runtime
Last reviewed: 2026-06-30

## Contents

- [Purpose](#purpose)
- [MVP Reality Check](#mvp-reality-check)
- [Prerequisites](#prerequisites)
- [Start the Runtime](#start-the-runtime)
- [Prepare Identity Fixtures](#prepare-identity-fixtures)
- [Prepare Human Test Sessions](#prepare-human-test-sessions)
- [Evidence Log](#evidence-log)
- [Test Matrix](#test-matrix)
- [Stop and Reset](#stop-and-reset)
- [References](#references)

## Purpose

This process gives a human tester an end-to-end path through the Phase 6
access-control MVP using real Keycloak authentication, the IAM Control Plane API,
and the protected `access-check-demo-service`. It covers login, logout, member
self-consultation, protected-service allow and deny behavior, admin member
management, super-admin-only operations, audit consultation, and evidence
capture.

## MVP Reality Check

The Phase 6 runtime does not include the Admin Console UI yet. Until that UI is
implemented, human e2e testing uses:

- Keycloak browser pages for real authentication and logout;
- bearer tokens obtained from the Keycloak-backed backoffice OIDC client;
- `curl` calls as the temporary operator surface for IAM Control Plane API
  actions;
- the real `access-check-demo-service` endpoint for protected-service access
  verification.

This is still a real e2e test of the accepted MVP authorization boundary. It is
not a final UX acceptance test for the missing Admin Console UI.

## Prerequisites

- Linux shell with Bash.
- Docker Engine with the Compose plugin.
- `curl`.
- `jq`.
- Python 3 for the local browser-login helper.
- A browser with separate profiles, containers, or private windows so the tester
  can keep `member`, `admin`, and `super-admin` sessions separate.
- A local `access-control/.env.local` created from `access-control/.env.example`
  with non-production fixture secrets.

All commands below run from the repository root.

## Start the Runtime

```bash
bash access-control/scripts/start.sh
bash access-control/scripts/bootstrap.sh
```

Verify basic reachability:

```bash
curl -fsS http://127.0.0.1:8000/healthz | jq .
curl -i http://127.0.0.1:8001/access-check-demo
```

Expected results:

- IAM health returns `{"status":"ok"}`.
- Demo service without a bearer token returns HTTP `401` and JSON
  `{"result":"KO","authorized":false}`.

Open Keycloak in a browser:

```text
http://127.0.0.1:8080
```

Use the local fixture usernames and passwords from `access-control/.env.local`.
Do not record passwords in test evidence.

## Prepare Identity Fixtures

Backoffice business accounts must be created through the IAM API, but Keycloak
still owns human identity, credentials, login sessions, and verified email
evidence in this MVP. For manual e2e testing, create Keycloak users as identity
fixtures only. Do not use direct Keycloak edits to create or mutate backoffice
business state.

Use the Keycloak Admin Console at `http://127.0.0.1:8080/admin/` with
`KC_BOOTSTRAP_ADMIN_USERNAME` and `KC_BOOTSTRAP_ADMIN_PASSWORD` from
`access-control/.env.local`.

In the `access-control-mvp` realm, prepare these users:

| Actor | Username | Email | Email verified | Password |
| --- | --- | --- | --- | --- |
| super-admin | `KEYCLOAK_SUPER_ADMIN_USERNAME` | `BOOTSTRAP_SUPER_ADMIN_EMAIL` | Already bootstrapped as verified | `KEYCLOAK_SUPER_ADMIN_PASSWORD` |
| admin | `human-admin-$E2E_RUN_ID` | `$ADMIN_EMAIL` from E2E-003 | Yes | Local test password |
| member | `human-member-$E2E_RUN_ID` | `$MEMBER_EMAIL` from E2E-005 | Yes | Local test password |

For the admin and member fixture users:

1. Create the Keycloak user in the `access-control-mvp` realm.
2. Set `Email verified` to `On`.
3. Set a non-temporary local test password.
4. Do not assign backoffice account-type roles or protected-service roles
   directly in Keycloak.

## Prepare Human Test Sessions

The IAM API and demo service need bearer access tokens from real Keycloak login
sessions. For this MVP, use the local browser-login helper:

```bash
python3 access-control/scripts/human-e2e-login.py \
  --output "$E2E_EVIDENCE_DIR/super-admin-token.json"
```

The helper prints a Keycloak authorization URL, listens only for the configured
localhost callback, exchanges the authorization code with PKCE, verifies the
returned OIDC nonce, and writes the token JSON to the requested output path.
Open the printed URL in the browser profile for the actor being tested.

Repeat the helper separately for `super-admin`, `admin`, and `member` sessions.
Store tokens only in shell variables for the active test terminal:

```bash
SUPER_ADMIN_TOKEN="$(jq -r '.accessToken' "$E2E_EVIDENCE_DIR/super-admin-token.json")"
ADMIN_TOKEN="$(jq -r '.accessToken' "$E2E_EVIDENCE_DIR/admin-token.json")"
MEMBER_TOKEN="$(jq -r '.accessToken' "$E2E_EVIDENCE_DIR/member-token.json")"
```

The token JSON includes a `logoutUrl`. Open that URL in the same browser profile
to perform Keycloak logout for that actor.

The human procedure is:

1. Use the helper URL to log in as the target actor through Keycloak.
2. Store the resulting access token only in a shell variable for the active test
   terminal.
3. Log out through the helper's `logoutUrl` before switching actors, or use
   separate browser profiles.

To prove logout behavior, after logging out in Keycloak, retry one request with
the old token:

```bash
curl -i -H "Authorization: Bearer $MEMBER_TOKEN" \
  http://127.0.0.1:8000/iam/me
```

Expected result:

- If the token is still unexpired, the API may still accept it because logout
  does not retroactively erase already-issued bearer tokens in this MVP runtime.
- After token expiry or when a revoked/invalid token is used, the API returns
  HTTP `401`.

Record this as a session-management limitation, not as proof of active-session
revocation. Production session revocation behavior is outside this MVP runtime
shortcut.

## Evidence Log

Create a local evidence note before testing:

```bash
E2E_RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
E2E_EVIDENCE_DIR="access-control/evidence/human-e2e-$E2E_RUN_ID"
mkdir -p "$E2E_EVIDENCE_DIR"
```

For each test case, record:

- tester name or initials;
- UTC timestamp;
- actor;
- browser profile or session used;
- command run or screen used;
- HTTP status;
- response body with tokens, passwords, secrets, cookies, and raw session values
  removed;
- pass/fail result;
- defect link or note when failed.

Collect runtime evidence after the manual pass:

```bash
bash access-control/scripts/collect-evidence.sh
```

Before sharing evidence outside the local test machine, remove token JSON files
or redact `accessToken`, `refreshToken`, `idToken`, and `logoutUrl` values.

To execute this checklist through Docker with prompts and a dedicated script
evidence log:

```bash
bash access-control/scripts/run-human-e2e.sh
```

To run the same script without pauses:

```bash
bash access-control/scripts/run-human-e2e.sh --yes
```

The Docker wrapper writes `docker-run.log` under
`access-control/evidence/human-e2e-docker-<timestamp>/`. The test container
writes `human-e2e-output.log` and `summary.json` under
`access-control/evidence/human-e2e-script-<timestamp>/`.

## Test Matrix

### E2E-001 Runtime Bootstrap

Goal: prove the local MVP runtime starts and bootstraps the first
`super-admin`.

Commands:

```bash
bash access-control/scripts/start.sh
bash access-control/scripts/bootstrap.sh
curl -fsS http://127.0.0.1:8000/healthz | jq .
```

Expected result:

- Bootstrap finishes successfully.
- IAM API health returns `status: "ok"`.
- The operation is idempotent when `bootstrap.sh` is repeated.

Feature coverage: `FR-008`, `FR-027`.

### E2E-002 Super-Admin Login and Self Profile

Goal: prove a human `super-admin` can authenticate through Keycloak and resolve
to the bootstrapped IAM account.

Commands:

```bash
curl -fsS -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
  http://127.0.0.1:8000/iam/me | jq .

curl -fsS -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
  http://127.0.0.1:8000/iam/me/services | jq .
```

Expected result:

- `/iam/me` returns an active `super-admin` account.
- `/iam/me/services` includes inherited protected-service access.

Feature coverage: `FR-004`, `FR-036`.

### E2E-003 Super-Admin Creates Admin

Goal: prove `super-admin` can create an invited `admin` account.

Command:

```bash
ADMIN_EMAIL="human-admin-$E2E_RUN_ID@example.test"

ADMIN_ACCOUNT_ID="$(
  curl -fsS -X POST http://127.0.0.1:8000/iam/accounts \
    -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$ADMIN_EMAIL\",\"organization\":\"MVP Organization\",\"name\":\"Human Admin\",\"accountType\":\"admin\"}" \
  | tee "$E2E_EVIDENCE_DIR/admin-create.json" \
  | jq -r '.accountId'
)"
```

Expected result:

- Response contains a stable `accountId`.
- The new account has `accountType: "admin"` and `lifecycle: "invited"`.

Feature coverage: `FR-008`, `FR-009`, `FR-018`, `FR-040`.

### E2E-004 Admin Onboarding Activation

Goal: prove the invited admin activates only after real Keycloak
authentication with matching verified email evidence and privileged OTP/ACR
evidence.

Steps:

1. Confirm the Keycloak admin fixture user exists with verified email matching
   `$ADMIN_EMAIL`.
2. Log in through Keycloak as that human admin user.
3. Complete the configured OTP step-up path for the admin session. The Docker
   script provisions a non-production OTP fixture credential and records only
   credential metadata plus the observed `iam-privileged` ACR; do not record OTP
   seed values in manual evidence.
4. Run the browser-login helper and set `ADMIN_TOKEN` from the resulting token
   JSON.
5. Activate onboarding:

```bash
curl -fsS -X POST http://127.0.0.1:8000/iam/onboarding/activate \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' | tee "$E2E_EVIDENCE_DIR/admin-activate.json" | jq .
```

Expected result:

- Response contains the same `$ADMIN_ACCOUNT_ID`.
- Lifecycle changes from `invited` to `active`.
- A linked subject is present.
- Privileged authentication evidence includes `acr: "iam-privileged"`.
- Repeating the activation with the same logged-in subject succeeds as
  `no_change`.

Feature coverage: `FR-010`, `FR-012`, `FR-039`, `FR-043`, `FR-044`.

### E2E-005 Admin Creates Member

Goal: prove an active `admin` can manage `member` accounts and cannot create
privileged accounts.

Commands:

```bash
MEMBER_EMAIL="human-member-$E2E_RUN_ID@example.test"

MEMBER_ACCOUNT_ID="$(
  curl -fsS -X POST http://127.0.0.1:8000/iam/accounts \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$MEMBER_EMAIL\",\"organization\":\"MVP Organization\",\"name\":\"Human Member\",\"accountType\":\"member\"}" \
  | tee "$E2E_EVIDENCE_DIR/member-create.json" \
  | jq -r '.accountId'
)"

curl -i -X POST http://127.0.0.1:8000/iam/accounts \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"blocked-admin-$E2E_RUN_ID@example.test\",\"organization\":\"MVP Organization\",\"name\":\"Blocked Admin\",\"accountType\":\"admin\"}" \
  | tee "$E2E_EVIDENCE_DIR/admin-create-admin-denied.txt"
```

Expected result:

- Member creation succeeds with `lifecycle: "invited"`.
- Admin-created admin account is rejected with HTTP `403`.

Feature coverage: `FR-007`, `FR-008`, `FR-017`, `FR-033`, `FR-040`.

### E2E-006 Member Onboarding and Self Profile

Goal: prove a member can activate through real authentication and read only
their own profile and effective services.

Steps:

1. Confirm the Keycloak member fixture user exists with verified email matching
   `$MEMBER_EMAIL`.
2. Log in through Keycloak as that member.
3. Run the browser-login helper and set `MEMBER_TOKEN` from the resulting token
   JSON.
4. Activate and read self-service endpoints:

```bash
curl -fsS -X POST http://127.0.0.1:8000/iam/onboarding/activate \
  -H "Authorization: Bearer $MEMBER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' | tee "$E2E_EVIDENCE_DIR/member-activate.json" | jq .

curl -fsS -H "Authorization: Bearer $MEMBER_TOKEN" \
  http://127.0.0.1:8000/iam/me \
  | tee "$E2E_EVIDENCE_DIR/member-me.json" | jq .

curl -fsS -H "Authorization: Bearer $MEMBER_TOKEN" \
  http://127.0.0.1:8000/iam/me/services \
  | tee "$E2E_EVIDENCE_DIR/member-services-before-role.json" | jq .

curl -i -H "Authorization: Bearer $MEMBER_TOKEN" \
  http://127.0.0.1:8000/iam/accounts \
  | tee "$E2E_EVIDENCE_DIR/member-list-accounts-denied.txt"
```

Expected result:

- Activation succeeds for the matching verified email subject.
- `/iam/me` returns only the current member account.
- `/iam/me/services` does not include demo access before assignment.
- Listing accounts as member is rejected with HTTP `403`.

Feature coverage: `FR-005`, `FR-019`, `FR-036`, `FR-037`, `FR-043`.

### E2E-007 Protected Demo Service Deny, Assign, Allow, Remove, Deny

Goal: prove protected-service access is enforced server-side through
`authorization/check`.

Commands:

```bash
curl -i -H "Authorization: Bearer $MEMBER_TOKEN" \
  http://127.0.0.1:8001/access-check-demo \
  | tee "$E2E_EVIDENCE_DIR/demo-before-role.txt"

curl -fsS -X PUT \
  "http://127.0.0.1:8000/iam/accounts/$MEMBER_ACCOUNT_ID/service-roles/access-check-demo:consult" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | tee "$E2E_EVIDENCE_DIR/member-role-assign.json" | jq .

curl -i -H "Authorization: Bearer $MEMBER_TOKEN" \
  http://127.0.0.1:8001/access-check-demo \
  | tee "$E2E_EVIDENCE_DIR/demo-after-role.txt"

curl -fsS -X DELETE \
  "http://127.0.0.1:8000/iam/accounts/$MEMBER_ACCOUNT_ID/service-roles/access-check-demo:consult" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | tee "$E2E_EVIDENCE_DIR/member-role-remove.json" | jq .

curl -i -H "Authorization: Bearer $MEMBER_TOKEN" \
  http://127.0.0.1:8001/access-check-demo \
  | tee "$E2E_EVIDENCE_DIR/demo-after-role-removal.txt"
```

Expected result:

- Before role assignment, the member gets HTTP `403` and `result: "KO"`.
- After assignment, the member gets HTTP `200` and `result: "OK"`.
- After removal, the member gets HTTP `403` and `result: "KO"` even if the
  browser still has a valid Keycloak session.

Feature coverage: `FR-002`, `FR-003`, `FR-005`, `FR-016`, `FR-020`, `FR-021`,
`FR-041`.

### E2E-008 Admin Lifecycle Management Stops Access

Goal: prove lifecycle changes stop protected-service access for a member.

Commands:

```bash
curl -fsS -X PUT \
  "http://127.0.0.1:8000/iam/accounts/$MEMBER_ACCOUNT_ID/service-roles/access-check-demo:consult" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq .

curl -fsS -X POST \
  "http://127.0.0.1:8000/iam/accounts/$MEMBER_ACCOUNT_ID/disable" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | tee "$E2E_EVIDENCE_DIR/member-disable.json" | jq .

curl -i -H "Authorization: Bearer $MEMBER_TOKEN" \
  http://127.0.0.1:8001/access-check-demo \
  | tee "$E2E_EVIDENCE_DIR/demo-after-member-disable.txt"

curl -fsS -X POST \
  "http://127.0.0.1:8000/iam/accounts/$MEMBER_ACCOUNT_ID/restore" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | tee "$E2E_EVIDENCE_DIR/member-restore.json" | jq .
```

Expected result:

- Disable succeeds.
- Disabled member receives HTTP `401` or `403` and `result: "KO"` from the demo
  service. `401` is acceptable when disabling the account also makes the
  Keycloak bearer token inactive; both outcomes are fail-closed access stop.
- Restore returns the member to `active`.

Feature coverage: `FR-013`, `FR-015`, `FR-016`, `FR-017`, `FR-021`.

### E2E-009 Super-Admin Service-Role Catalog Operation

Goal: prove only `super-admin` can mutate the service-role catalog.

Commands:

```bash
curl -fsS -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://127.0.0.1:8000/iam/service-roles \
  | tee "$E2E_EVIDENCE_DIR/admin-service-roles-list.json" | jq .

curl -i -X POST http://127.0.0.1:8000/iam/service-roles \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"roleId\":\"access-check-demo:human-$E2E_RUN_ID\",\"serviceId\":\"access-check-demo-service\",\"name\":\"Human E2E Role\"}" \
  | tee "$E2E_EVIDENCE_DIR/admin-service-role-create-denied.txt"

curl -fsS -X POST http://127.0.0.1:8000/iam/service-roles \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"roleId\":\"access-check-demo:human-$E2E_RUN_ID\",\"serviceId\":\"access-check-demo-service\",\"name\":\"Human E2E Role\"}" \
  | tee "$E2E_EVIDENCE_DIR/super-admin-service-role-create.json" | jq .

curl -fsS -X POST \
  "http://127.0.0.1:8000/iam/service-roles/access-check-demo:human-$E2E_RUN_ID/disable" \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
  | tee "$E2E_EVIDENCE_DIR/super-admin-service-role-disable.json" | jq .

curl -fsS -X POST \
  "http://127.0.0.1:8000/iam/service-roles/access-check-demo:human-$E2E_RUN_ID/archive" \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
  | tee "$E2E_EVIDENCE_DIR/super-admin-service-role-archive.json" | jq .
```

Expected result:

- Admin can list service roles.
- Admin cannot create service roles and receives HTTP `403`.
- Super-admin can create a service role.
- The run-scoped service role is disabled and archived after creation so the
  runtime catalog does not keep active human-e2e artifacts.

Feature coverage: `FR-004`, `FR-032`, `FR-033`.

### E2E-010 Super-Admin Audit Consultation

Goal: prove audit consultation is restricted to `super-admin`.

Commands:

```bash
curl -i -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://127.0.0.1:8000/iam/audit/events \
  | tee "$E2E_EVIDENCE_DIR/admin-audit-denied.txt"

curl -fsS -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
  http://127.0.0.1:8000/iam/audit/events \
  | tee "$E2E_EVIDENCE_DIR/super-admin-audit-events.json" | jq .
```

Expected result:

- Admin audit read is rejected with HTTP `403`.
- Super-admin audit read succeeds.
- Returned events include entries for account creation, onboarding, role
  assignment or removal, authorization denial, and the audit read itself.

Feature coverage: `FR-027`, `FR-028`, `FR-035`.

### E2E-011 Logout and Actor Isolation

Goal: prove the tester can separate human actor sessions and avoid accidental
cross-actor evidence.

Steps:

1. In the member browser profile, use Keycloak logout.
2. In the admin browser profile, confirm the admin session remains separate.
3. In a fresh private window, open Keycloak and confirm the user must log in.
4. Retry `/iam/me` with no bearer token.

Command:

```bash
curl -i http://127.0.0.1:8000/iam/me \
  | tee "$E2E_EVIDENCE_DIR/no-token-me-denied.txt"
```

Expected result:

- Fresh unauthenticated browser session requires login.
- IAM API without a bearer token returns HTTP `401`.
- Evidence clearly labels which actor token was used for each API call.

Feature coverage: `FR-036`, `FR-037`.

## Stop and Reset

Stop without deleting state:

```bash
bash access-control/scripts/stop.sh
```

Delete local runtime state only when the evidence has been collected and the
tester intentionally wants a clean environment:

```bash
RESET_CONFIRM=delete-access-control-mvp-state bash access-control/scripts/reset.sh
```

## References

- [Access-Control MVP Runtime](./README.md)
- [MVP Scope - Access-Control Production MVP](../docs/evaluation/mvp-scope.md)
- [IAM Control Plane API Contract](../docs/architecture/iam-control-plane-api-contract.md)
- [Feature Requirements Specification](../FEATURE-REQUIREMENTS.md)
