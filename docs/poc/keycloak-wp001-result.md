# Keycloak WP-001 Result

Status: Review
Phase: Phase 4 - Proof of Concept
Scope: PoC
Last reviewed: 2026-06-05

## Contents

- [Summary](#summary)
- [Commands Verified](#commands-verified)
- [Observed Result](#observed-result)
- [Evidence](#evidence)
- [Limitations](#limitations)
- [References](#references)

## Summary

`WP-001` was executed against the scripted [Keycloak PoC runtime](../../poc/keycloak/README.md) on 2026-06-05. The runtime uses Docker Compose and Keycloak `start-dev`, which is acceptable only for the non-production Phase 4 validation boundary ([Keycloak setup runbook](./keycloak-setup-runbook.md), [Project governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept), [Keycloak container guide](https://www.keycloak.org/server/containers)).

Result: pass for the initial Keycloak setup validation. The realm, OIDC client, non-production users, event settings, and OIDC discovery checks were created or verified by scripts. This validates `WP-001`; it does not validate `WP-002` login/SSO behavior, onboarding, `authorization/check`, access-stop behavior, audit correlation, or production readiness ([Keycloak validation plan - Work Packages](./keycloak-validation-plan.md#work-packages)).

After user direction, the PoC scripts were restored to use `jq` for JSON construction, parsing, validation, and evidence formatting. The jq-backed scripts were rerun successfully with `jq-1.8.1`, and `WP-001` still passed. A second full retest was executed successfully on the same scripted path, producing the latest evidence directory below.

## Commands Verified

The following commands were executed with the PoC environment template:

```bash
jq --version
ENV_FILE=poc/keycloak/.env.example bash poc/keycloak/scripts/start.sh
ENV_FILE=poc/keycloak/.env.example bash poc/keycloak/scripts/bootstrap.sh
ENV_FILE=poc/keycloak/.env.example bash poc/keycloak/scripts/verify.sh
ENV_FILE=poc/keycloak/.env.example bash poc/keycloak/scripts/collect-evidence.sh
ENV_FILE=poc/keycloak/.env.example bash poc/keycloak/scripts/stop.sh
```

`docker compose --env-file poc/keycloak/.env.example -f poc/keycloak/compose.yaml config` also passed, proving that the Compose file resolves to a valid Keycloak service definition for this PoC runtime.

## Observed Result

| Check | Result |
| --- | --- |
| Keycloak container startup | Pass |
| OIDC discovery for `master` realm | Pass |
| Realm `edrlab-backoffice-poc` creation | Pass |
| Client `backoffice-bff-poc` creation | Pass |
| Authorization Code flow enabled | Pass |
| Implicit Flow disabled | Pass |
| Direct Access Grants disabled | Pass |
| Redirect URI configured | Pass |
| Web origin configured | Pass |
| User `kc-member-poc` exists | Pass |
| User `kc-admin-poc` exists | Pass |
| User `kc-super-admin-poc` exists | Pass |
| User `kc-unsafe-poc` exists | Pass |
| Unsafe user email remains unverified | Pass |
| User events enabled | Pass |
| Admin events enabled | Pass |
| Admin event details enabled | Pass |
| Runtime stopped after verification | Pass |

## Evidence

The scripted evidence collector wrote local generated evidence to:

```text
poc/keycloak/evidence/20260605T145102Z
```

Generated evidence is ignored by Git by default. The evidence directory contained:

- `discovery.json`
- `client.json`
- `users.json`
- `events-config.json`
- `compose-ps.txt`
- `keycloak-logs-tail.txt`
- `wp-001-evidence.md`

## Limitations

- The verification used `.env.example` placeholder values to prove runtime behavior. Real local execution should copy `.env.example` to ignored `.env.local` and replace placeholder secrets before use ([Keycloak PoC runtime - Setup](../../poc/keycloak/README.md#setup)).
- The runtime uses Keycloak `start-dev`; this is not production deployment evidence ([Keycloak container guide](https://www.keycloak.org/server/containers)).
- `WP-001` does not prove browser login, BFF session behavior, onboarding activation, privileged-authentication evidence, claim override rejection, protected-service authorization, access-stop behavior, or local audit correlation. Those remain later work packages in the accepted plan ([Keycloak validation plan - Work Packages](./keycloak-validation-plan.md#work-packages)).

## References

- [Keycloak Validation Plan](./keycloak-validation-plan.md)
- [Keycloak Setup Runbook](./keycloak-setup-runbook.md)
- [Keycloak PoC Runtime](../../poc/keycloak/README.md)
- [Project Governance - Phase 4](../../PROJECT-GOVERNANCE.md#phase-4---proof-of-concept)
- [Keycloak Container Guide](https://www.keycloak.org/server/containers)
- [Keycloak OIDC Endpoints and Grant Types](https://www.keycloak.org/securing-apps/oidc-layers)
