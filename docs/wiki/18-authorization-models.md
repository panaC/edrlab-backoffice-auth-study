# Authorization Models

Authorization models describe how a system represents and evaluates access: who can do which action on which resource under which conditions.

This page compares the main authorization models used in industry: RBAC, ABAC, ReBAC, policy-based authorization, ACLs, scopes, claims, entitlements, and hybrid models. It is conceptual study material and does not choose a final model for this project.

## Why it matters

Authorization vocabulary should be clear before evaluating products or building proofs of concept. Otherwise every access-control mechanism gets called "RBAC" or "scopes" even when the real model needs roles, permissions, resource ownership, attributes, relationships, policy rules, or a combination.

This page is for engineers who need to model authorization for internal applications, administration APIs, and backend services. It explains which root problem each model solves, how OAuth2 scopes and token claims relate to application permissions, and what practices tend to work or fail in industry systems.

## Core authorization question

Most runtime authorization decisions can be reduced to this shape:

```text
Can principal P perform action A on resource R in context C?
```

Examples:

| Principal | Action | Resource | Context |
| --- | --- | --- | --- |
| `member:123` | `members:disable` | `member:456` | Internal backoffice session |
| `service:billing-sync` | `reports:write` | `report:daily-revenue` | Scheduled worker |
| `member:789` | `documents:view` | `document:abc` | Organization `org:acme` |

The model determines where the answer comes from: role assignment, permission table, attributes, relationships, policy rules, token claims, or a policy decision service.

## Model families

| Model | Core idea | Solves well | Common weakness |
| --- | --- | --- | --- |
| RBAC | Users or subjects receive roles; roles contain permissions. | Human administrative access, job functions, simple internal applications. | Role explosion, coarse permissions, weak fit for object-level sharing. |
| Permission-based access | Subjects or roles map to explicit operations such as `members:read`. | Clear API enforcement and auditability. | Needs naming discipline and lifecycle ownership. |
| ABAC | Decisions use attributes of subject, resource, action, and environment. | Contextual access, department, region, risk, time, tenant, resource status. | Attribute quality and policy complexity can become hard to govern. |
| ReBAC | Decisions use relationships between subjects and objects. | Sharing, ownership, groups, folders, teams, parent-child resources, collaboration. | Requires relationship modeling and synchronization with business data. |
| ACL | A resource stores a list of subjects or groups allowed to access it. | Direct object sharing and simple resource-level grants. | Hard to audit and manage at scale without hierarchy or central tooling. |
| PBAC or policy-based access | Policies express allow or deny decisions over structured inputs. | Centralized, testable, expressive authorization logic. | Policy lifecycle and input modeling become critical operational work. |
| OAuth2 scopes | A client requests limited delegated access. | API delegation and token request constraints. | Not a complete user authorization model by itself. |
| Token claims | Access facts are embedded in tokens. | Fast local checks by resource servers. | Stale until token expiry and easy to misuse if validation is weak. |
| Entitlements | A named grant that permits a capability, feature, package, or account right. | SaaS packaging, licensing, plan-based access, feature access. | Can blur product packaging with security authorization. |

## RBAC

Role-Based Access Control groups permissions into roles and assigns roles to users or subjects. NIST's RBAC model describes roles, permissions, sessions, role hierarchies, and constraints such as separation of duty.

RBAC is usually a good starting point for an internal backoffice because the actors are often humans with recognizable job functions: support, finance, operations, security administrator, viewer, and so on.

### Best use

- Administrator-created users.
- Small to medium internal teams.
- Operation-level backend permissions grouped into reviewable roles.
- Access reviews where humans need to understand why someone has access.

### Common failure mode

RBAC fails when roles become vague containers for everything: `admin`, `super_admin`, `manager`, `internal`, `billing_access`. A role should explain why a subject has a set of permissions; it should not replace the permission catalog.

## Permission-based access

Permission-based access names the concrete operations that resource servers enforce.

Examples:

| Permission | Meaning |
| --- | --- |
| `members:read` | Read member profile and lifecycle state. |
| `members:disable` | Disable an internal member account. |
| `roles:assign` | Assign an existing role to a member. |
| `clients:rotate_secret` | Rotate an OAuth client credential. |
| `audit:read` | Read IAM audit events. |

This model is often combined with RBAC: roles are human-friendly bundles; permissions are the API-facing enforcement units.

## ABAC

Attribute-Based Access Control evaluates attributes about the subject, resource, action, and environment. NIST SP 800-162 defines ABAC as using such attributes against policies, rules, or relationships.

Examples:

- support agents may only view tickets in their assigned region;
- export operations are denied outside office network ranges;
- a member can update a resource only when `resource.status != "locked"`;
- administrators need step-up authentication for high-risk actions.

### Best use

- Context-dependent authorization.
- Resource metadata matters.
- Environmental factors matter, such as network, time, device posture, session assurance, or risk.
- The policy can be tested and explained.

### Common failure mode

ABAC becomes fragile when attributes are stale, untrusted, poorly typed, or fetched from many runtime services without latency and outage design.

## ReBAC

Relationship-Based Access Control evaluates access through relationships between subjects and objects. The best-known industrial reference is Google's Zanzibar paper, which describes a global system for storing and evaluating access control lists with a uniform data model used by many Google services. OpenFGA and SpiceDB are open-source Zanzibar-inspired systems.

Examples:

- a user can view a document if they are an owner, editor, viewer, or member of a team that has access;
- a user can administer a project if they administer the parent organization;
- a service can access a resource if it belongs to the same workspace.

### Best use

- Collaboration and sharing.
- Object-level authorization.
- Inherited access through teams, organizations, folders, projects, or parent resources.
- "Who can access this?" and "What can this user access?" queries.

### Common failure mode

ReBAC is overkill when all permissions are coarse backoffice operations. It introduces an authorization graph, a relationship write path, consistency choices, schema testing, and a critical runtime dependency.

## Policy-based authorization

Policy-based authorization externalizes decision logic into policies. OPA uses Rego and accepts structured input. Cedar, used by Amazon Verified Permissions, models principals, actions, resources, entity data, context, and policies.

Policy-based systems are useful when authorization rules need to be reviewed, tested, versioned, and changed independently of application code.

For the deeper industry-oriented explanation of OPA, Cedar, Verified Permissions, OpenFGA, SpiceDB, and Zanzibar-style systems, see [Policy Engines and Fine-Grained Authorization](./21-policy-engines-and-fine-grained-authorization.md).

### Best use

- Multi-service authorization rules that need common governance.
- ABAC-style contextual decisions.
- Compliance-sensitive policy review.
- Product logic that benefits from simulation and policy testing.

### Common failure mode

A policy engine can become an expert-only second application if the team does not define policy ownership, deployment, test fixtures, observability, and rollback.

## OAuth2 scopes and token claims

OAuth2 scopes and token claims are important, but they are not full authorization models by themselves.

| Concept | Correct use | Mistake to avoid |
| --- | --- | --- |
| Scope | Limits what a client is allowed to request or use in a token. | Treating scopes as complete user permissions without checking user access and resource context. |
| Claim | Carries a trusted assertion inside a token after validation. | Trusting claims from an unvalidated JWT or using ID-token claims as API authorization. |
| Role claim | Allows an API to make fast local role checks. | Assuming role changes are immediate while long-lived tokens still carry old roles. |
| Permission claim | Allows an API to enforce operation-level permissions locally. | Putting too many changing permissions in long-lived tokens. |
| Audience claim | Identifies the intended resource server. | Accepting tokens minted for a different API. |

For simple backoffice RBAC, permission claims in short-lived access tokens can be practical if the stale-access window is acceptable. If role changes must take effect immediately, consider short token lifetimes, introspection, or an authorization-check API.

## Hybrid model

Most industrial systems combine models:

```text
Workforce or application identity source
  -> RBAC roles for human administration
  -> explicit API permissions for enforcement
  -> attributes for context and restrictions
  -> optional ReBAC for object relationships
  -> optional policy engine for complex decisions
```

Hybrid is normal. The important design rule is to know which model owns each fact. Do not store the same role, permission, relationship, and entitlement in several systems without a source of truth.

## Best practices

- Start with the operation: name the protected action before choosing the model.
- Keep authentication separate from authorization.
- Use stable subject identifiers, not mutable emails, in authorization records.
- Define a permission catalog that backend APIs can enforce.
- Use roles as bundles of permissions, not as hidden business logic.
- Keep high-risk admin actions explicit, narrow, and audited.
- Validate tokens before reading claims.
- Decide whether permissions in tokens may be stale until token expiry.
- Keep policy and relationship models testable before production use.
- Design for deny-by-default and least privilege.

## Common mistakes

- Treating `admin` as the only authorization model.
- Using frontend route guards as the final enforcement layer.
- Accepting any JWT without issuer, audience, signature, and expiry validation.
- Using OAuth2 scopes as a shortcut for product permissions without a clear mapping.
- Mixing customer entitlements, internal administrator permissions, and infrastructure roles in one vocabulary.
- Giving service accounts human administrator roles.
- Duplicating role assignments in the IdP, application database, and business services without reconciliation.
- Choosing ReBAC or a policy engine because it sounds more advanced, not because the resource model needs it.
- Building custom authorization logic without tests for deny cases and privilege escalation.

## Industry patterns and critique

| Industry pattern | Common products or systems | Critique |
| --- | --- | --- |
| Directory groups to app roles | Microsoft Entra, Okta, Google Workspace groups. | Useful for workforce lifecycle, but directory groups often become too broad or reused to be precise application permissions. |
| IdP roles or permissions in tokens | Auth0 RBAC, Keycloak roles, Okta authorization server claims. | Good for simple APIs, but token staleness and claim shape must be understood. |
| Cloud IAM policies | AWS IAM, Google Cloud IAM, Azure RBAC. | Excellent reference models for infrastructure access, but cloud resource hierarchy can be too heavy for small application authorization. |
| Policy-as-code | OPA/Rego, Cedar, Amazon Verified Permissions. | Strong for policy governance and ABAC-style logic, but does not replace IdP, token issuance, lifecycle, or enforcement points. |
| Zanzibar-style permissions | Google Zanzibar, OpenFGA, SpiceDB. | Strong for relationship-heavy products; usually unnecessary for simple internal role administration. |
| Local app RBAC | Framework middleware and application database tables. | Simple and effective for one application; risky when multiple clients, APIs, or identity sources appear. |

## What this means for this study

For a minimal internal backoffice IAM Control Plane, the likely baseline to evaluate is:

- RBAC for human administrator access;
- explicit operation-level permissions;
- server-side enforcement in the IAM Control Plane Admin API and backend APIs;
- OAuth2/OIDC claims or introspection only after token validation;
- no relationship-heavy authorization system unless a concrete resource-sharing requirement appears;
- no external policy engine unless authorization rules become complex enough to justify its operational cost.

This is not a final recommendation. It is a vocabulary and evaluation frame for later phases.

## Related pages

- [RBAC](./05-rbac.md)
- [PDP, PEP, PIP, and PAP](./17-pdp-pep-pip-pap.md)
- [Policy Engines and Fine-Grained Authorization](./21-policy-engines-and-fine-grained-authorization.md)
- [IAM Data Model](./22-iam-data-model.md)
- [IAM Responsibility Model](./16-iam-responsibility-model.md)
- [IAM Architecture](./15-iam-architecture.md)
- [Tokens and JWTs](./04-tokens-and-jwt.md)
- [OAuth2](./02-oauth2.md)
- [Security Best Practices](./09-security-best-practices.md)

## References

- [NIST - The NIST Model for Role-Based Access Control: Towards a Unified Standard](https://www.nist.gov/publications/nist-model-role-based-access-control-towards-unified-standard)
- [NIST SP 800-162 - Guide to Attribute Based Access Control Definition and Considerations](https://csrc.nist.gov/pubs/sp/800/162/upd2/final)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [RFC 6749 - The OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749)
- [RFC 7519 - JSON Web Token](https://www.rfc-editor.org/rfc/rfc7519)
- [Google Zanzibar paper](https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/)
- [Open Policy Agent documentation](https://www.openpolicyagent.org/docs/latest)
- [Amazon Verified Permissions - What is Amazon Verified Permissions?](https://docs.aws.amazon.com/verifiedpermissions/latest/userguide/what-is-avp.html)
- [Cedar Policy Language Reference Guide](https://docs.cedarpolicy.com/)
- [OpenFGA Introduction](https://openfga.dev/docs/fga)
- [OpenFGA Concepts](https://openfga.dev/docs/concepts)
- [SpiceDB Documentation](https://authzed.com/docs)
