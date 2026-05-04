# Admin API

## What it is

The administration API is the privileged management surface for IAM data. It is where administrators and approved automation manage members, roles, permissions, clients, service accounts, and assignments.

For this study, the administration API should be understood as a protected resource server with extra risk. It changes who can authenticate, who can access systems, which clients can receive tokens, and which service accounts can call internal APIs.

This page is conceptual. It describes capabilities and risks without choosing a product, storage design, endpoint shape, or deployment architecture.

## Why it matters

The backoffice authorization system is administrator-managed. Public account registration is out of scope. That means the administration API is not an optional convenience; it is part of the control plane.

If the admin API is weakly protected, attackers or ordinary users may be able to create accounts, assign roles, issue clients, disable users, or grant service access. Those operations can be more sensitive than ordinary application data because they change the security boundary for every backoffice service.

## How it works

The administration API should require authentication and explicit administrator authorization. A token that proves login is not enough. Each operation needs an authorization check against a permission such as `members:create`, `members:disable`, `roles:assign`, or `clients:write`.

Core resources include:

| Resource | Example operations |
| --- | --- |
| Members | Create, read, update, disable, delete, list. |
| Roles | Create, read, list, update, delete where appropriate. |
| Permissions | List, describe, map to roles. |
| Role assignments | Assign and remove roles from members or service accounts. |
| Clients | Register, read, update, disable, rotate credentials. |
| Service accounts | Create, disable, assign permissions, rotate credentials. |
| Authorization checks | Check whether a member or service has a required role or permission. |
| Audit events | Record privileged changes and access decisions where useful. |

Example conceptual endpoint map:

| Operation | Example permission |
| --- | --- |
| `POST /members` | `members:create` |
| `GET /members` | `members:read` |
| `PATCH /members/{id}` | `members:write` |
| `POST /members/{id}/disable` | `members:disable` |
| `GET /roles` | `roles:read` |
| `POST /roles` | `roles:create` |
| `POST /members/{id}/roles` | `roles:assign` |
| `DELETE /members/{id}/roles/{role}` | `roles:assign` |
| `POST /authorization/check` | `authorization:check` |

The endpoint names are examples only. Later phases may choose different API shapes or use existing admin APIs from an identity product.

## Admin authorization checks

Admin checks should be server-side, explicit, and operation-specific. A member with `members:read` should not be able to assign roles. A member with `roles:assign` may still need restrictions that prevent self-escalation, such as assigning `admin` to themselves or creating a client with broader powers than they possess.

The API should handle disabled members and disabled clients consistently. A disabled subject should not continue to manage IAM data just because it still has a cached UI state.

The admin API may need stronger operational controls than ordinary APIs:

- audit logging for privileged changes;
- rate limits or abuse controls for sensitive endpoints;
- concurrency and idempotency behavior for role assignment;
- validation that prevents duplicate or contradictory state;
- clear error behavior that avoids leaking unnecessary sensitive data;
- separation between read-only administration and mutation privileges.

## Audit and accountability

Audit logs should make privileged changes explainable. A useful record usually includes actor, subject, action, target resource, result, timestamp, request identifier, source context, and before/after fields where safe and appropriate.

Audit logging is not just for compliance. It helps answer operational questions after mistakes: who disabled this member, who granted this role, which service created this client, and when did a credential rotate?

Sensitive values such as passwords, secrets, refresh tokens, and full bearer tokens should not be logged.

## Standards context

SCIM defines a standard model and protocol for cross-domain identity management. It can be useful background for user and group provisioning concepts, but this Phase 1 page does not recommend adopting SCIM. OAuth2 Dynamic Client Registration defines a way to register OAuth2 clients dynamically, but an internal admin API may choose different controls later.

The useful lesson is that identity administration has established patterns and risks. Custom admin APIs need conservative design because small mistakes can become privilege escalation paths.

## Example

An administrator creates a member for Alice, assigns the `support` role, and later disables Alice's account after she leaves the company.

The API validates the administrator's access token for each request. It checks `members:create` for the create operation, `roles:assign` for role assignment, and `members:disable` for disabling the account. Each mutation writes an audit event. If the administrator lacks one permission, that operation is denied even if other admin operations are allowed.

## Common mistakes

Protecting the admin UI but not the admin API leaves the true control plane exposed.

Using one broad `admin` permission for every operation makes least privilege and audit review harder.

Allowing administrators to grant privileges they do not hold can enable accidental or malicious escalation.

Failing to audit changes makes incident response and access reviews much weaker.

Returning secrets after creation or writing them to logs increases credential exposure.

Treating deletion, disabling, and revocation as the same thing can cause operational confusion. They have different audit, recovery, and security implications.

## References

- [RFC 7009 - OAuth 2.0 Token Revocation](https://www.rfc-editor.org/rfc/rfc7009)
- [RFC 7591 - OAuth 2.0 Dynamic Client Registration Protocol](https://www.rfc-editor.org/rfc/rfc7591)
- [RFC 7643 - System for Cross-domain Identity Management: Core Schema](https://www.rfc-editor.org/rfc/rfc7643)
- [RFC 7644 - System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644)
- [OWASP API Security Top 10](https://owasp.org/API-Security/)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
- [NIST SP 800-63-4 - Digital Identity Guidelines](https://pages.nist.gov/800-63-4/)
