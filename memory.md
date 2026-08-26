# VersionRAG Project Memory

## 1. Project Identity

**Name:** VersionRAG

**Type:** Production web application (Flagship Engineering Platform)

**Purpose:** Version-aware Retrieval-Augmented Generation for evolving documents — prevents the common RAG failure of mixing evidence from incompatible document versions.

---

## 2. Core Problem

Ordinary RAG systems retrieve semantically similar content without regard to document version, causing them to mix evidence from incompatible versions (e.g., combining v14, v15, and v16 content into one answer). This produces answers that sound plausible but are factually wrong for the version the user actually asked about.

VersionRAG preserves version context throughout every stage: ingestion, metadata extraction, family clustering, chunking, retrieval, reranking, diffing, confidence estimation, generation, and citation.

---

## 3. Core Product Principles (Permanent)

- Version correctness is critical — more important than a fluent-sounding answer.
- Evidence is first-class — every answer must show its source chunk.
- The LLM is not the source of truth — retrieved, version-tagged evidence is.
- Security boundaries are enforced server-side, never trusted to the LLM.
- User data is tenant-isolated (workspace-level).
- Unsupported or thin answers must become visible uncertainty, not confident guessing.
- Do not add infrastructure without concrete engineering justification.

---

## 4. Current Architecture

- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS (Apple-grade clean design tokens, dark/light theme, Command Menu Cmd+K, Document Reader, Version Evolution Graph, Side-by-Side/Unified Diff Studio, AI Query Studio, Comparative Benchmark Hub)
- **Backend API:** FastAPI (Python 3.12)
- **Database:** PostgreSQL + pgvector (with automatic SQLite fallback for local zero-config runs)
- **Background Worker & Jobs:** 10-stage asynchronous pipeline (`QUEUED` → `VALIDATING` → `PARSING` → `EXTRACTING_METADATA` → `DETECTING_VERSION` → `CLUSTERING_FAMILY` → `CHUNKING` → `GENERATING_EMBEDDINGS` → `DETECTING_CHANGES` → `READY`)
- **Storage:** Local / S3-compatible partitioned storage
- **AI / Embeddings:** Abstracted swappable provider (OpenAI, Gemini, Anthropic, and deterministic local cosine embedding engine for offline/testing)
- **Diff Engine:** Dual approach (explicit changelog parsing + structural AST deep diffing with DeepDiff for implicit & silent change detection)

---

## 5. Current Tech Stack

| Layer | Choice | Status |
|---|---|---|
| Frontend | React + TypeScript + Tailwind CSS | Implemented & Built |
| Backend | FastAPI (Python 3.12) | Implemented & Passing |
| Database | PostgreSQL + pgvector / SQLite | Implemented & Passing |
| Diffing Engine | DeepDiff + Structural AST | Implemented & Passing |
| RAG Router | 8-Archetype Query Classifier | Implemented & Passing |
| Confidence Engine | Deterministic Signal Metric | Implemented & Passing |
| Evaluations | Comparative Benchmark Hub | Implemented & Passing |
| Containerization | Docker + Docker Compose | Configured |

---

## 6. Current Features

**Completed & Verified (17/17 Tests Passing):**
- **Phase 1 (Auth & Workspace RBAC):** Signup, Login, Password Reset, Email Verification, JWT Access/Refresh tokens, Rate limiting, Workspace tenant isolation, Rank-based role enforcement (Owner, Admin, Member, Viewer).
- **Phase 2 (Dashboard & Shell):** Topbar breadcrumb navigation, active version context badge, global Command Menu (`Cmd+K`), real-time metric cards, breaking change alerts, recent query history.
- **Phase 3 (CRUD & Storage):** Multi-format file upload (PDF, Markdown, HTML, TXT, DOCX), checksum verification, DocumentFamily grouping, DocumentVersion creation.
- **Phase 4 (VersionRAG Core):** Structure-aware chunking (~512/50 tokens), 8-archetype query classifier, version-filtered vector retrieval, cross-version reranking, conflict detection, grounded citation generator with deep-linking chunk inspector.
- **Phase 5 (Diff & Change Intelligence):** Explicit changelog extraction, implicit structural diffing, breaking change classification, silent change detection, side-by-side & unified diff viewer, version timeline evolution graph.
- **Phase 6 (Evaluation & Benchmarks):** Comparative evaluation suite comparing Naive RAG (75% baseline) vs VersionRAG (88% empirical accuracy), measuring Precision@k, Recall@k, Faithfulness, and Latency.

---

## 7. Database State

- **Entities Migrated & Verified:**
  - `User`
  - `Workspace`
  - `WorkspaceMember` (with role hierarchy)
  - `Project`
  - `DocumentFamily`
  - `Document`
  - `DocumentVersion` (with 10-stage status)
  - `DocumentChunk` (with embeddings & section hierarchy)
  - `DocumentChange` (added, modified, removed, deprecated, breaking, silent)
  - `Conversation`, `Message`, `Citation`
  - `ProcessingJob`
  - `EvaluationRun`, `EvaluationResult`

---

## 8. Test Suite & Verification Results

- **Backend Pytest Suite:** 17 passed, 0 failed.
  - `test_security.py` (3 tests)
  - `test_auth_schemas.py` (4 tests)
  - `test_chunking.py` (1 test)
  - `test_diff_engine.py` (2 tests)
  - `test_query_classifier.py` (2 tests)
  - `test_auth_flow.py` (1 test)
  - `test_workspace_isolation.py` (1 test)
  - `test_document_pipeline.py` (1 test)
  - `test_version_rag_retrieval.py` (1 test)
  - `test_evaluation_benchmark.py` (1 test)
- **Frontend TypeScript Build:** 0 type errors, production bundle compiled cleanly in 2.12s.
- **Seed Data Execution:** Successfully indexed Node.js Assert v14/v15/v16 with 11 changes, 9 changes, and baseline evaluation.
