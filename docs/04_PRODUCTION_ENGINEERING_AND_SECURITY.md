# 🔒 04. Production Engineering, Security & Reliability

---

## 1. Production Authentication & Real Gmail SMTP Architecture

VersionRAG includes a **production-distributable authentication system** that rejects fake verification:

```
[ User Registers ] ──► [ Generate 6-Digit OTP ] ──► [ Bcrypt Hash (Salt=12) ] ──► [ Save to DB ]
                                                                                         │
[ Account Verified ] ◄── [ Validate OTP ] ◄── [ Real Gmail SMTP with TLS ] ◄─────────────┘
```

### Key Security Implementations:
1. **Gmail App Password Support:** Transports over `smtp.gmail.com:587` with explicit `STARTTLS` encryption.
2. **Cryptographic OTP Storage:** 6-digit numeric codes are hashed via `bcrypt` with automatic 15-minute expiration windows.
3. **Strict Verification Enforcement:** Accounts remain in `is_verified = False` state until the code is validated; unauthorized login attempts return `HTTP 403 Forbidden` (`EMAIL_NOT_VERIFIED`).
4. **Rate Limiting & Anti-Enumeration:** Registration and login endpoints use token bucket rate limiting (5 attempts / 60 seconds) with constant-time password verification to prevent timing attacks.

---

## 2. Multi-Tenant Workspace & Project Isolation

Data isolation is guaranteed across organizational boundaries:
- **Tenant Scope:** Each `Workspace` owns isolated `Project` tracks.
- **Foreign Key Cascades:** Deleting a document family safely purges all associated version chunks, AST nodes, and diff records without orphaned vectors.
- **Row-Level Partition Filters:** All SQL and vector queries enforce tenant predicates:
  ```python
  query = db.query(DocumentChunk).filter(
      DocumentChunk.project_id == current_project_id,
      DocumentChunk.version_tag == requested_version_tag
  )
  ```

---

## 3. Resilient Database Layer: PostgreSQL `pgvector` with SQLite Fallback

To support both enterprise production clusters and lightweight local evaluation, the database layer provides automatic multi-driver adaptation:

```python
# Automatic Vector Index Dialect Adapter
if db_url.startswith("sqlite"):
    # Local lightweight in-memory / file fallback for portable testing
    connect_args = {"check_same_thread": False}
    engine = create_engine(db_url, connect_args=connect_args, poolclass=StaticPool)
else:
    # Production enterprise PostgreSQL cluster with pgvector extension
    engine = create_engine(db_url, echo=False, pool_pre_ping=True, pool_size=10, max_overflow=20)
```

---

## 4. Automated Test Suite (100% Passing)

The backend is backed by an automated Pytest test suite covering unit schemas, diffing logic, RAG retrieval, and integration lifecycles:

```
============================= test session starts =============================
backend/tests/integration/test_auth_flow.py::test_full_auth_lifecycle           PASSED [  5%]
backend/tests/integration/test_document_pipeline.py::test_document_upload...     PASSED [ 11%]
backend/tests/integration/test_evaluation_benchmark.py::test_evaluation...     PASSED [ 17%]
backend/tests/integration/test_version_rag_retrieval.py::test_version_aware...  PASSED [ 23%]
backend/tests/integration/test_workspace_isolation.py::test_tenant_isolation... PASSED [ 29%]
backend/tests/unit/test_auth_schemas.py::test_user_create_validation_success    PASSED [ 35%]
backend/tests/unit/test_auth_schemas.py::test_user_create_password_too_short    PASSED [ 41%]
backend/tests/unit/test_auth_schemas.py::test_user_create_password_missing_up.. PASSED [ 47%]
backend/tests/unit/test_auth_schemas.py::test_user_create_password_missing_dig.. PASSED [ 52%]
backend/tests/unit/test_chunking.py::test_structure_aware_chunking               PASSED [ 58%]
backend/tests/unit/test_diff_engine.py::test_explicit_changelog_extraction       PASSED [ 64%]
backend/tests/unit/test_diff_engine.py::test_implicit_silent_change_detection   PASSED [ 70%]
backend/tests/unit/test_query_classifier.py::test_query_archetype_routing       PASSED [ 76%]
backend/tests/unit/test_query_classifier.py::test_confidence_insufficient_evi.. PASSED [ 82%]
backend/tests/unit/test_security.py::test_password_hashing_and_verification      PASSED [ 88%]
backend/tests/unit/test_security.py::test_token_type_safety                     PASSED [ 94%]
backend/tests/unit/test_security.py::test_expired_token                         PASSED [100%]
============================= 17 passed in 5.33s ==============================
```

---

👉 *Continue to [05. Interview Deep Dive](05_INTERVIEW_DEEP_DIVE.md).*
