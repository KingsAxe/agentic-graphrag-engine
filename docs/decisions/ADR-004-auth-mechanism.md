# ADR-004: Authentication Mechanism

**Status:** Proposed  
**Date:** 2026-03-30  
**Deciders:** Engineering Lead

---

## Context

SovereignRAG V2 plans for multi-user workspaces in V2.3. Authentication is not a V2.3 concern —
it is a day-one concern, because the auth mechanism determines how request identity is established,
how data is isolated between users, and what the PostgreSQL schema looks like from the first
migration.

Choosing the wrong mechanism now creates a hard migration later, particularly around workspace
data isolation. This ADR defines the options and their implications for the full system.

---

## Decision Drivers

- Must support multi-tenancy: each workspace's documents, graph nodes, and embeddings must be
  scoped to their owner
- Must be simple enough to implement in V2.1 without blocking infrastructure work
- Must be extensible to support human user auth in V2.3 without requiring schema changes
- Must not require an external identity provider in Phase 1
- Must be stateless at the API Gateway level (no server-side sessions)

---

## Options Considered

### Option A: API Key per Workspace

Each workspace is assigned a static API key at creation time. All requests include the key in
the `Authorization: Bearer <key>` header. The gateway looks up the key, resolves the workspace
ID, and injects it into the request context. No user concept exists at this stage — the workspace
is the principal.

**Database model:**
```sql
workspaces (
    id          UUID PRIMARY KEY,
    name        TEXT NOT NULL,
    api_key     TEXT UNIQUE NOT NULL,   -- hashed, like bcrypt
    created_at  TIMESTAMPTZ NOT NULL,
    is_active   BOOLEAN DEFAULT TRUE
)
```

| Factor | Assessment |
|---|---|
| Implementation complexity | Very low |
| Statelessness | Full — key lookup is a DB read |
| Multi-tenancy support | Yes — workspace_id is the isolation boundary |
| User-level auth | Not supported — one key per workspace, no user identity |
| Token rotation | Manual — requires key regeneration endpoint |
| Expiry / revocation | Yes — via is_active flag |
| V2.3 extensibility | Moderate — adding user auth requires schema additive changes |
| External dependency | None |

**Risks:** API keys are long-lived credentials. If leaked, the entire workspace is exposed until
the key is rotated. No per-user audit trail. Suitable for programmatic access and internal
tooling but insufficient for a user-facing product.

---

### Option B: JWT-Based User Auth (from day one)

Users register and log in. Successful login returns a signed JWT (access token, short expiry)
and a refresh token (long expiry, stored in the database). Every request carries the access JWT.
The gateway verifies the signature without a DB call. Workspace membership is encoded in the
token claims.

**Token payload:**
```json
{
  "sub": "user_id",
  "workspace_ids": ["ws_abc123"],
  "role": "owner",
  "exp": 1735000000
}
```

**Database model:**
```sql
users (
    id              UUID PRIMARY KEY,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL
)

workspaces (
    id              UUID PRIMARY KEY,
    name            TEXT NOT NULL,
    owner_id        UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL
)

workspace_members (
    workspace_id    UUID REFERENCES workspaces(id),
    user_id         UUID REFERENCES users(id),
    role            TEXT NOT NULL,    -- owner, editor, viewer
    PRIMARY KEY (workspace_id, user_id)
)

refresh_tokens (
    id              UUID PRIMARY KEY,
    user_id         UUID REFERENCES users(id),
    token_hash      TEXT UNIQUE NOT NULL,
    expires_at      TIMESTAMPTZ NOT NULL,
    revoked         BOOLEAN DEFAULT FALSE
)
```

| Factor | Assessment |
|---|---|
| Implementation complexity | Medium — token issuance, refresh, revocation all required |
| Statelessness | Full for access token verification |
| Multi-tenancy support | Full — workspace membership in token claims |
| User-level auth | Yes — per-user identity and audit trail |
| Token rotation | Automatic via refresh token flow |
| Expiry / revocation | Yes — per-token and per-user |
| V2.3 extensibility | High — schema is already complete |
| External dependency | None — self-contained |

**Risks:** More code to write in V2.1. Password reset and email verification flows are
additional work. Refresh token storage adds a stateful component.

---

### Option C: API Key for V2.1, Migrate to JWT for V2.3

Implement API key auth as a clean, isolated middleware layer. Design the workspace schema to
be additive-compatible with a future user table. When V2.3 begins, add JWT auth alongside
API key auth (both supported simultaneously) and deprecate API keys.

**Migration path:**
```
V2.1: workspace created -> api_key issued -> all requests use api_key
V2.3: user table added -> workspace gains owner_id FK (nullable initially)
      -> JWT auth layer added alongside API key layer
      -> existing workspaces migrated to user accounts
      -> API key auth deprecated
```

| Factor | Assessment |
|---|---|
| V2.1 implementation complexity | Very low |
| V2.3 migration complexity | Medium — nullable FK, dual-auth middleware period |
| Risk of breaking changes | Low if schema is designed carefully now |
| Schema design discipline required | High — owner_id must be reserved as a nullable column from day one |

**Risks:** Dual-auth middleware in V2.3 is additional complexity. If the schema is not
designed correctly now, the migration will require destructive changes.

---

## Comparison Summary

| Criterion | API Key | JWT from Day One | API Key -> JWT |
|---|---|---|---|
| V2.1 dev effort | Lowest | Medium | Lowest |
| User-level identity | No | Yes | No (until V2.3) |
| Audit trail | Workspace-level | User-level | Workspace-level until V2.3 |
| Schema complexity | Low | High | Low (now), Medium (V2.3) |
| Long-term correctness | No | Yes | Yes (if migration planned) |
| Credential security | Moderate | High | Moderate (until V2.3) |

---

## Recommendation

**Option C: API Key for V2.1, planned migration to JWT in V2.3.**

The system is not user-facing in V2.1 and V2.2. Implementing full JWT auth now adds
meaningful development overhead without delivering user value yet. However, the PostgreSQL schema
must be designed from day one with the V2.3 migration in mind — specifically, the `workspaces`
table must include a nullable `owner_id` column that will be populated when user accounts
are introduced.

The auth middleware layer must be isolated behind an interface so that the JWT implementation
can be swapped in without touching any service code.

---

## Decision

**[ ] API Key only**  
**[ ] JWT-Based User Auth from day one**  
**[ ] API Key for V2.1, migrating to JWT in V2.3 (recommended)**  

_Mark the selected option and update status to "Accepted" when decided._
