# Operational Model

This document records the operational topics the internal backoffice IAM study must evaluate before a final recommendation or production implementation.

This document originated as Phase 1 study material and now supports Phase 2 requirements definition. It does not choose a hosting provider, database, logging stack, monitoring tool, backup product, incident-response process, or production runbook.

## Purpose

The IAM control plane is security-critical infrastructure. It authenticates users, issues tokens, stores member and role state, manages OAuth clients, and records privileged audit evidence. A small user count does not make operations optional.

The operational model should answer:

- who owns the IAM service;
- what state must be backed up and restored;
- how upgrades and migrations are handled;
- how signing keys, client secrets, and service credentials are rotated;
- what monitoring and alerts are required;
- how incidents are detected, contained, recovered, and reviewed;
- whether break-glass access is needed and how it is controlled.

## Ownership map

| Responsibility | Owner to define | Evidence to expect |
| --- | --- | --- |
| IAM control-plane ownership | Team accountable for design and runtime operation. | Architecture decision records, change approvals, escalation path. |
| Member administration | People allowed to create, disable, restore, and recover members. | Admin procedure, audit events, access request records. |
| Role and permission ownership | Service or IAM owners who approve permission meaning. | Permission catalog, role review records. |
| OAuth client ownership | Team or service owner for each client. | Client inventory with owner, purpose, environment, allowed flows. |
| Secret and key ownership | Operators responsible for key rotation and secret handling. | Rotation records, key inventory, emergency procedure. |
| Audit and review ownership | Team allowed to read/export audit evidence and run reviews. | Review cadence, export procedure, retention decision. |
| Incident response | People who can contain credential, token, admin, or provider incidents. | Incident runbooks, contact list, lessons learned. |

For fewer than 1,000 users, the process can be lightweight. The risky state is not "small team"; it is "no named owner".

## State inventory

The project should classify IAM state before evaluating self-hosted, managed, or hybrid options.

| State | Examples | Backup and recovery concern |
| --- | --- | --- |
| Member data | Stable IDs, status, email, profile metadata. | Losing it can break login, authorization, and audit traceability. |
| Authorization data | Roles, permissions, assignments, grant boundaries. | Restore must preserve current access and historical assignments. |
| OAuth client data | Client IDs, redirect URIs, allowed flows, environments, owners. | Incorrect restore can allow wrong callbacks or block legitimate clients. |
| Credentials and authenticators | Password hashes, passkey metadata, MFA enrollment, recovery metadata. | Sensitive; backup access is high impact. |
| Token and session state | Refresh tokens, server-side BFF sessions, revocation records. | May be intentionally invalidated during restore or incident response. |
| Signing keys | JWT signing private keys and public JWKS metadata. | Loss can break token issuance; compromise can require emergency rotation. |
| Client secrets and service credentials | Shared secrets, private-key references, certificate metadata. | Must be protected, rotated, and never exposed in ordinary reads. |
| Audit logs | Privileged changes, denied attempts, token/client/key events. | Must survive incidents and remain reviewable. |
| Configuration | Issuer, audiences, token lifetimes, password/MFA policy, redirect settings. | Drift can produce security failures or outages. |
| Runbooks | Restore, rotation, incident, break-glass, and review procedures. | Operators need them during stress, not after. |

## Backups

Backups are security controls and availability controls. For an IAM system, backups also become sensitive credential-adjacent assets.

Baseline expectations:

- back up IAM data, authorization data, client metadata, configuration, and audit logs;
- decide whether BFF sessions and refresh-token stores are backed up or intentionally treated as disposable;
- encrypt backups and restrict restore privileges;
- keep backup access separate from ordinary application read access;
- record backup success and failure in monitoring;
- test restores on a schedule;
- document recovery point objective and recovery time objective before production;
- preserve stable IDs so audit and role assignments remain meaningful after restore;
- avoid restoring stale access unintentionally after an incident.

For incident recovery, the team may decide to restore member and role data while invalidating sessions and refresh tokens. That should be a documented mode, not an improvised decision.

## Restore behavior

Restore is where backup quality becomes real. A useful IAM restore test should prove:

| Check | Success condition |
| --- | --- |
| Data integrity | Members, roles, assignments, clients, and audit events restore with stable IDs intact. |
| Secret handling | Restored secrets and keys are protected; old leaked credentials are not reintroduced. |
| Token behavior | Existing sessions and refresh tokens are either restored intentionally or invalidated intentionally. |
| Issuer continuity | Resource servers can still validate tokens after restore, or the outage behavior is documented. |
| Audit continuity | Restore actions are recorded and post-restore audit evidence remains available. |
| Access review | Restored admin access and client credentials are reviewed after major recovery. |

A restore runbook should include who can authorize restore, which backups are eligible, how to verify integrity, how to rotate credentials if compromise is suspected, and how to communicate expected login or token disruption.

## Upgrades and migrations

The operational model must differ for managed, self-hosted, minimal-library, and hybrid options, but the evaluation questions are similar:

- How are security patches applied?
- Can upgrades be tested against a staging environment?
- Are database migrations reversible or at least recoverable from backup?
- Does the product publish migration notes for clients, tokens, roles, and provider metadata?
- What happens to active sessions and refresh tokens during upgrade?
- How are signing keys and JWKS metadata preserved across upgrade?
- Can the team roll back safely without restoring stale access?
- Which smoke tests prove login, token issuance, token validation, admin API authorization, audit events, and access checks still work?

For managed providers, the team still owns configuration review, release awareness, integration testing, and incident response for provider-side changes that affect the backoffice.

## Key and credential rotation

Key rotation is a planned process, not just a button.

| Asset | Rotation concern |
| --- | --- |
| JWT signing keys | Publish new public keys before use; keep old public keys until old tokens expire; retire old keys after the overlap window. |
| Client secrets | Generate high-entropy secrets, show once, support rollout windows, retire old secrets, audit metadata. |
| Private key JWT credentials | Register new public keys, roll clients gradually, retire old keys. |
| mTLS certificates | Manage issuance, renewal, trust anchors, expiration, and service rollout. |
| Password hash parameters | Migrate gradually on login or through a controlled rehash process. |
| Backup encryption keys | Protect and rotate without making old backups unrecoverable unintentionally. |
| Break-glass credentials | Keep dormant, protected, tested, and reviewed without making them routine admin accounts. |

Emergency rotation should exist for compromise. Planned rotation should exist for hygiene and operability.

## Monitoring and alerts

IAM monitoring should cover security signals and operational health.

| Signal | Why it matters |
| --- | --- |
| Login failure spikes | Possible brute force, password spraying, provider outage, or UX regression. |
| Admin authorization denials | Possible probing, misconfiguration, or attempted escalation. |
| Role assignment and removal | High-impact access changes. |
| Client creation, redirect URI update, or secret rotation | Changes token issuance trust boundaries. |
| Token validation failures by reason | Wrong issuer, wrong audience, expired token, invalid signature, or stale JWKS indicate different problems. |
| Refresh-token rejection or reuse detection | Possible token theft, user logout, or provider policy behavior. |
| Disabled member login attempts | Useful for offboarding validation and incident review. |
| Audit logging failure | Loss of evidence; should be high priority. |
| Backup failure or restore-test failure | Recovery capability is degraded. |
| Signing-key rotation state | Prevents outages from missing JWKS propagation or retired keys. |
| Latency and error rate for token, admin, and introspection endpoints | IAM outages can block many services. |

Alerts should have owners and runbooks. An alert without an action path becomes noise.

## Incident response

Incident response for IAM should be prepared before production. Useful scenario playbooks include:

| Scenario | Immediate containment questions |
| --- | --- |
| Stolen access token | Which API audience is affected? How long until expiry? Can introspection or revocation reject it now? |
| Stolen refresh token | Which client and member are affected? Can the refresh token or grant be revoked? Are sessions ended? |
| Client secret leak | Which client and environment? Can the secret be rotated without outage? Were tokens minted after leak? |
| Signing key compromise | Which tokens can be forged? Can the key be retired? How will APIs refresh JWKS? |
| Compromised administrator | Which roles, clients, members, and audit exports did the admin touch? Can access be suspended and reviewed? |
| Bad role assignment | Who received access, which tokens may contain it, and when does it stop? |
| Broken audience validation | Which APIs accepted wrong tokens? Which logs show misuse? |
| Provider or IAM outage | Can existing sessions continue? Can admins recover? Which services fail closed or degrade? |

The response loop should include detection, analysis, containment, eradication, recovery, communication, and lessons learned. The project should not wait for a production incident to decide who can revoke tokens, disable clients, rotate keys, or activate break-glass access.

## Break-glass access

Break-glass is emergency access for restoring or managing the IAM control plane when normal paths fail. It can prevent lockout, but it can also become a permanent bypass if poorly designed.

If production needs break-glass, evaluate these controls:

- very small number of emergency paths;
- stronger authentication and protected recovery material;
- dormant by default where possible;
- explicit activation reason;
- time-bound access;
- alert on activation;
- separate audit event family;
- post-use review;
- tested recovery procedure;
- no routine daily administration through break-glass.

The final design may decide not to include break-glass. That is acceptable only if lockout and provider outage risks are explicitly accepted or mitigated another way.

## Readiness checklist

Before production, the team should be able to show:

- current owner for IAM operations;
- member, role, client, and service-account inventory;
- backup schedule and successful restore evidence;
- signing-key and client-secret rotation procedure;
- monitoring dashboards or alerts for core IAM signals;
- incident playbooks for token, client, key, admin, and provider incidents;
- break-glass decision and procedure if adopted;
- access review process for administrators, roles, clients, and future service accounts;
- documented token and session lifecycle behavior;
- audit export and retention expectations.

## Related documents

- [Auditability, Access Reviews, and Operational Ownership](./wiki/10-auditability-access-reviews-operational-ownership.md)
- [Token Lifecycle](./wiki/12-token-lifecycle.md)
- [OAuth Client Management](./wiki/13-oauth-client-management.md)
- [BFF Sessions and Token Handling](./bff-sessions-and-token-handling.md)
- [Member Lifecycle](./member-lifecycle.md)
- [Initial Permission Model](./initial-permission-model.md)
- [Threat Model](./threat-model.md)

## References

- [NIST Cybersecurity Framework 2.0](https://www.nist.gov/publications/nist-cybersecurity-framework-csf-20)
- [NIST SP 800-61 Rev. 3 - Incident Response Recommendations and Considerations for Cybersecurity Risk Management](https://csrc.nist.gov/pubs/sp/800/61/r3/final)
- [NIST SP 800-34 Rev. 1 - Contingency Planning Guide for Federal Information Systems](https://csrc.nist.gov/pubs/sp/800/34/r1/final)
- [NIST SP 800-53 Rev. 5 - Security and Privacy Controls for Information Systems and Organizations](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)
- [NIST SP 800-57 Part 1 Rev. 5 - Recommendation for Key Management](https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final)
- [NIST SP 800-92 - Guide to Computer Security Log Management](https://csrc.nist.gov/pubs/sp/800/92/final)
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
