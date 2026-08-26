# phase1-implementation-report.md
### VersionRAG — Phase 1: Login & Authentication — Implementation Report

**Status: Phase 1 core auth + workspace logic implemented, tested against a real Postgres + Redis instance, and passing.**

This file documents what was ACTUALLY built and verified — not planned. Per `memory.md`'s own rule: never write "implemented" unless it's implemented and verified.

---

## 1. What Was Built

### Backend structure created
```
backend/
├── app/
│   ├── core/
│   │   ├── config.py          # env-based settings
│   │   ├── security.py        # password hashing + JWT (access/refresh/verify/reset tokens)
│   │   ├── deps.py             # auth guards + workspace-membership authorization
│   │   └── rate_limit.py       # Redis-backed login rate limiting
│   ├── models/
│   │   ├── base.py             # shared UUID + timestamp mixin
│   │   ├── user.py
│   │   └── workspace.py        # Workspace + WorkspaceMember + role enum
│   ├── schemas/
│   │   ├── auth.py             # signup/login/reset request+response schemas
│   │   └── workspace.py
│   ├── services/
│   │   ├── auth_service.py     # business logic, separate from routes
│   │   └── email_service.py    # HONESTLY STUBBED — logs instead of sending real email
│   ├── api/v1/
│   │   ├── auth.py              # signup, login, logout, refresh, verify, reset routes
│   │   └── workspaces.py        # create/list/get/delete workspace, list members
│   └── main.py
├── migrations/
│   └── versions/0001_initial_auth_and_workspaces.py
└── tests/
    ├── unit/            (15 tests)
    └── integration/     (12 tests)
```

### Features actually working, verified end-to-end
- User signup with password strength validation (min 10 chars, uppercase, digit)
- Duplicate-email rejection (generic error message — doesn't leak which emails are registered)
- Login issuing an access token (30 min) + refresh token (7 days)
- Token refresh flow
- Password reset request + completion (token-based, single-purpose, time-limited)
- Email verification (token-based)
- Protected routes reject missing/invalid tokens
- Workspace creation, gated behind email verification
- Workspace membership roles (Owner/Admin/Member/Viewer) with rank-based authorization
- **Cross-workspace data isolation** — a non-member gets 404 (not 403) so workspace existence isn't leaked
- Only an Owner can delete a workspace — a Member gets rejected
- Login rate limiting: 5 failed attempts per email per 60 seconds, then HTTP 429

---

## 2. Test Results (Actually Run, Not Estimated)

**Environment:** Real PostgreSQL 16 + real Redis 7, installed directly in the sandbox (Docker wasn't available here, so services were installed and run natively instead of skipping verification).

```
27 passed, 0 failed
- 15 unit tests   (security.py logic, schema validation — no DB/network)
- 12 integration tests (full HTTP request → DB → response, real Postgres + Redis)
```

Test files:
- `tests/unit/test_security.py` — password hashing, token type-safety (a refresh token can't be used as an access token, etc.)
- `tests/unit/test_auth_schemas.py` — password/email/name validation rules
- `tests/integration/test_auth_flow.py` — signup → login → refresh → protected-route flow, rate limiting
- `tests/integration/test_workspace_isolation.py` — the security-critical tenant-isolation tests

---

## 3. Real Bugs Found and Fixed (This Is the Actual Engineering Work)

Documenting these honestly because catching and fixing them — not the absence of bugs — is what proves the code was actually run, not just written and assumed correct.

### Bug 1 — bcrypt/passlib version incompatibility
**Symptom:** Every single password hash crashed with `ValueError: password cannot be longer than 72 bytes`.
**Root cause:** passlib 1.7.4 depends on an internal bcrypt attribute (`__about__.__version__`) that was removed in bcrypt ≥4.1.
**Fix:** Pinned `bcrypt==4.0.1` explicitly in `requirements.txt` instead of leaving it unpinned.

### Bug 2 — Alembic enum double-creation
**Symptom:** Migration failed with `DuplicateObject: type "workspace_role" already exists`.
**Root cause:** The migration explicitly created the Postgres ENUM type, then `create_table`'s `before_create` event tried to auto-create the same type again.
**Fix:** Added `create_type=False` on the column-level ENUM reference so it reuses the already-created type instead of recreating it.

### Bug 3 — Enum case mismatch between Python and Postgres
**Symptom:** `DataError: invalid input value for enum workspace_role: "OWNER"`.
**Root cause:** SQLAlchemy defaults to sending a Python enum's `.name` (`"OWNER"`) to the database, but the Postgres enum type stores lowercase values (`"owner"`).
**Fix:** Added `values_callable=lambda enum_cls: [m.value for m in enum_cls]` to the SQLAlchemy `Enum` column definition.

### Bug 4 — Test isolation gap via shared Redis state
**Symptom:** The rate-limit test failed intermittently depending on what had run against Redis previously.
**Root cause:** Redis counters from `app/core/rate_limit.py` persisted across test runs since nothing cleared them.
**Fix:** Added an `autouse` pytest fixture that flushes the test Redis database before and after every test.

---

## 4. Known, Honest Limitations (Not Hidden)

1. **Email sending is stubbed, not real.** `email_service.py` logs what would be sent instead of using real SMTP. This is explicitly commented in the code itself so it's never mistaken for a working feature later.
2. **Logout doesn't invalidate tokens server-side.** Since this uses stateless JWTs, "logout" currently just tells the client to discard its tokens. A stolen access token remains valid until it naturally expires (30 min). A proper fix (refresh-token denylist in Redis) is a known, tracked gap — not silently ignored.
3. **OAuth (Google/GitHub login) is not implemented.** The architecture allows adding it later without a redesign, but it doesn't exist yet.
4. **Docker Compose setup exists but wasn't verified end-to-end in this session** because Docker itself wasn't available in this sandbox — Postgres/Redis were installed and run natively instead to actually verify the code, which is a reasonable substitute but not identical to verifying the real container setup.

---

## 5. Definition of Done Checklist (from `phases.md` Phase 1)

- [x] User can sign up, verify email, log in, log out, reset password
- [x] Sessions are secure and expire appropriately
- [x] All non-auth routes reject unauthenticated requests
- [x] Workspace membership model exists and is enforced
- [x] Unit tests for password hashing, token generation/validation, and route protection
- [ ] `memory.md` updated — **not yet done, should be the immediate next step**

---

## 6. Immediate Next Steps

1. Update `memory.md` Sections 6, 7, 8, 12, and 17 with this real status (currently `memory.md` still says "nothing implemented yet" — that's now out of date and should be corrected, not left stale).
2. Verify the existing `docker-compose.yml` actually builds and runs this code in containers (was not confirmed this session).
3. Begin Phase 2 (Dashboard) per `phases.md`.
