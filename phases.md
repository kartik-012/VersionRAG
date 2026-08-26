# phases.md
### VersionRAG — Breakdown of the Project into Manageable Phases

This file exists so that development happens in a controlled, verifiable order — one phase is fully working before the next begins. It follows on from `architecture.md` (how the system is designed), `design.md` (how it looks and behaves), and `memory.md` (what has actually been done so far).

**Rule that applies to every phase below:** a phase is not "done" because code compiles. It is done when: it works end-to-end, it has tests, it has error handling, it has loading/failure states in the UI, and `memory.md` has been updated to reflect it honestly.

---

## PHASE 1: LOGIN & AUTHENTICATION

### Goal
A real user can create an account, sign in, sign out, and reset their password — with proper session security and workspace membership wired up. Nothing AI-related happens yet.

### 1.1 User Registration
- Sign-up form: email, password, name.
- Server-side validation: email format, password strength minimum, duplicate-email rejection.
- Email verification flow (send verification link/token, mark account verified on click).
- Do not allow unverified accounts to create a workspace (or clearly gate what they can do until verified — decide and document the choice in `memory.md`'s ADR log).

### 1.2 Login / Logout
- Login form: email + password.
- Secure password hashing (bcrypt/argon2 — never plaintext, never reversible encryption).
- Session handling via secure, httpOnly cookies or short-lived JWT + refresh token (pick one, document the choice).
- Logout clears the session/token fully — not just client-side state.
- Rate-limit login attempts to reduce brute-force risk.

### 1.3 Password Reset
- "Forgot password" flow: request reset → emailed token → reset form → confirm.
- Reset tokens are single-use and time-limited.
- After reset, all existing sessions for that user should be invalidated.

### 1.4 Authentication & Authorization Setup
- Protected routes: any workspace/project/document route requires a valid session.
- Authorization is enforced server-side on every request — never trust a frontend-only route guard.
- Workspace membership check: a user can only access a workspace's data if they are a member of it (ties directly into `architecture.md` Section 6 — Workspaces).
- Roles established at this phase even if not fully used yet: Owner / Admin / Member / Viewer.
- Architecture should allow adding OAuth providers (Google/GitHub login) later without a redesign — don't build it now, just don't block it.

### Phase 1 Definition of Done
- [ ] User can sign up, verify email, log in, log out, reset password
- [ ] Sessions are secure and expire appropriately
- [ ] All non-auth routes reject unauthenticated requests
- [ ] Workspace membership model exists and is enforced
- [ ] Unit tests for password hashing, token generation/validation, and route protection
- [ ] `memory.md` updated: Section 6 (Features), Section 7 (Current Work), Section 17 (Session Handoff)

---

## PHASE 2: DASHBOARD

### Goal
A logged-in user sees a real, useful overview of their workspace — not a static welcome screen.

### 2.1 Dashboard Layout
- Implements the application shell from `design.md` Section 6: sidebar, top bar, main content area.
- Workspace switcher functional (even with just one workspace initially).

### 2.2 Overview Cards / Stats
Per `design.md` Section 7, show (with real data, not placeholders):
- Recent projects
- Recent documents (with live processing status)
- Version activity (recently added versions)
- Recent queries (empty at this phase, since AI querying isn't built yet — show the correct empty state)
- Detected changes (empty at this phase — show the correct empty state)

### 2.3 Navigation Setup
- Sidebar items wired to real routes, even if some routes are still placeholder pages at this point: Workspace, Projects, Documents, Versions, Changes, Queries, Evaluations, Settings.
- Breadcrumb component functional and reflects actual navigation depth.

### 2.4 Basic Data Visualization
- Simple, honest visualizations only — e.g., a document/version count summary, a processing-status breakdown (Ready / Processing / Failed counts).
- No fabricated or placeholder charts — if there's no data yet, show the empty state, not a fake chart with sample numbers.

### Phase 2 Definition of Done
- [ ] Dashboard renders real counts from the database, not hardcoded numbers
- [ ] All sidebar links navigate correctly
- [ ] Empty states appear correctly when no data exists yet
- [ ] Responsive behavior verified on mobile/tablet per `design.md` Section 22
- [ ] `memory.md` updated

---

## PHASE 3: CRUD OPERATIONS

### Goal
Full lifecycle management of the core entities: Workspace, Project, Document, and DocumentVersion. This is the data backbone everything else depends on.

### 3.1 Create, Read, Update, Delete — Main Entities

**Workspace:** create, rename, delete (with confirmation — deleting a workspace deletes everything under it, so this must be explicit per `design.md` Section 24 Rule 7).

**Project:** create (scoped to a workspace), rename, update description, delete.

**Document:** upload (drag/drop + file picker per `design.md` Section 9), rename, delete, view metadata.

**DocumentVersion:** created automatically during ingestion (not manually typed by the user in the normal flow), but must support manual correction if version/family detection got it wrong (per `architecture.md` Section 11).

### 3.2 Form Validation
- Every create/edit form validates both client-side (fast feedback) and server-side (source of truth — never trust client validation alone).
- File upload validation: file type allowlist (PDF, Markdown, TXT, HTML per `architecture.md` Section 7.1), file size limits, malformed file rejection with a clear error message.

### 3.3 List & Detail Views
- Document list view: uses the Document Card component from `design.md` Section 9.
- Document detail view: shows version list/timeline per `design.md` Section 10.
- Project detail view: shows documents, recent activity.
- Pagination for any list that could grow large (documents, versions, changes).

### 3.4 Search, Filter & Sort
- Document list: filter by processing status, sort by name/date/version count.
- Global search (Command Menu, per `design.md` Section 5) across documents at minimum at this phase — versions/changes search comes in later phases once those entities have real content.

### Phase 3 Definition of Done
- [ ] Full CRUD works for Workspace, Project, Document
- [ ] File upload validated and stored (original file accessible per `architecture.md` Section 8)
- [ ] Document processing pipeline triggers on upload (async job queued — even if the job itself is still a stub at this phase)
- [ ] List views paginate, filter, and sort correctly
- [ ] Integration tests: upload → record created → appears in list
- [ ] `memory.md` updated

---

## PHASE 4: ADDITIONAL FEATURES (The VersionRAG-Specific Core)

### Goal
This is where VersionRAG becomes VersionRAG rather than a generic document manager. This phase is intentionally the largest — it corresponds to Phases 2–4 of the roadmap in `architecture.md`.

### 4.1 Business Logic & Rules — Version Intelligence
- Metadata extraction pipeline: LLM reads first pages, extracts title/version/type, stored with `detected_value / confidence / source` (per `architecture.md` Section 9) — never silently invented.
- Version parsing: must handle non-semver formats (`v14`, `2025.01`, `2025-Q1`) per `architecture.md` Section 10 — use deterministic parsing/regex where possible, LLM only where necessary (per design principle: don't use AI where deterministic logic works better).
- Document family detection: group versions of the same evolving document using title + metadata + semantic similarity signals (`architecture.md` Section 11), with manual override support.
- Chunking: ~512 tokens / ~50 overlap baseline, structure-aware exceptions for headings/code/tables (`architecture.md` Section 13).
- Embedding generation and version-tagged storage in pgvector (`architecture.md` Section 14).

### 4.2 File Upload / Download (already partially built in Phase 3, extended here)
- Original file remains downloadable at any time (per `architecture.md` Section 8).
- New version upload flow: attaches to existing document family, triggers incremental processing (only diffs against the immediately previous version, per `architecture.md` Section 39 — not a full rebuild).

### 4.3 Change Detection Engine
- Explicit: parse changelogs/release notes when present.
- Implicit: DeepDiff-based comparison between consecutive versions + LLM-generated human-readable summary (`architecture.md` Section 18).
- Change record storage per the schema in `architecture.md` Section 19.
- Version Comparison UI (`design.md` Section 11) and Change Timeline UI (`design.md` Section 12) become functional here, using real data.

### 4.4 The AI Query Interface (the flagship feature)
- Query classification into the 8 types (`architecture.md` Section 16 / `design.md` Section 13).
- Version-aware retrieval pipeline: Query Understanding → Version/Date/Intent Detection → Retrieval Strategy Selection → Candidate Retrieval → Version Filtering → Reranking → Evidence Validation → Context Assembly → LLM (`architecture.md` Section 15).
- Confidence scoring built from real signals, not a raw LLM self-report (`architecture.md` Section 25 / `design.md` Section 17).
- Conflict detection and display when versions disagree (`architecture.md` Section 24 / `design.md` Section 15–16).
- Citation UI wired to real evidence chunks, clickable through to the Document Reader.

### 4.5 Notifications / Alerts
- In-app notification when: a document finishes processing, a processing job fails, a breaking change is detected in a new version.
- Keep this simple at first (in-app toast + notification center) — do not build email/push notifications unless there's a real need identified later.

### 4.6 Settings / Preferences
- Project-level settings: default query scope, notification preferences.
- Account-level settings: profile info, password change.
- Workspace-level settings: member management, roles (per `design.md` Section 8).

### Phase 4 Definition of Done
- [ ] A user can upload multiple versions of a real document and the system correctly separates and links them
- [ ] Asking a version-specific question returns evidence only from the correct version
- [ ] Change detection surfaces both explicit and implicit changes with a working timeline
- [ ] Confidence states appear and are derived from real signals (documented in `memory.md` Section 10)
- [ ] Citations are clickable and traceable to source
- [ ] `memory.md` Section 10 (AI/RAG State) fully updated with actual implementation details — not planned/TBD anymore

---

## PHASE 5: TESTING & QUALITY ASSURANCE

### Goal
Confidence that the system behaves correctly and predictably — this phase is not optional polish, it's what makes the flagship claims defensible in an interview.

### 5.1 Unit Testing
- Metadata extraction logic
- Version string parsing (including non-semver formats)
- Chunking logic
- Diff/change-detection logic
- Query classification logic
- Confidence scoring calculation

### 5.2 Integration Testing
- Full upload → processing → indexing pipeline
- Full question → retrieval → answer → citation pipeline
- Cross-workspace isolation (a user in Workspace A can never retrieve Workspace B's data — per `architecture.md` Section 36, this gets an explicit security test, not just a hope)

### 5.3 Bug Fixing
- Maintain the Known Issues log in `memory.md` Section 12 — every bug found gets an entry (severity, status, root cause once known, next action) rather than being fixed silently and forgotten.

### 5.4 Performance Testing
- Measure and record (in `memory.md` Section 14, never fabricated): retrieval latency, LLM response latency, embedding generation time, end-to-end question-answering time.
- Load-test the incremental processing logic specifically — confirm that uploading version 6 of a document with 5 existing versions does NOT reprocess all 5 (per `architecture.md` Section 39).

### 5.5 The Evaluation Benchmark (this project's most important test)
- Build the benchmark dataset described in `architecture.md` Section 13: content, version-specific, comparison, change, historical, silent-change, and conflicting-version questions.
- Run Naive RAG vs. your VersionRAG implementation on this dataset.
- Record real accuracy numbers in `memory.md` Section 14.
- Compare honestly against the original paper's published numbers (90% VersionRAG / 58% naive RAG) — note where you match, exceed, or fall short, and why.

### Phase 5 Definition of Done
- [ ] Test suite covers unit, integration, and security cases listed above
- [ ] All known bugs are logged and triaged, not silently ignored
- [ ] Real performance numbers recorded (not estimated)
- [ ] Evaluation benchmark run and results recorded honestly, including any shortfalls
- [ ] `memory.md` Sections 12 and 14 fully updated

---

## PHASE 6: DEPLOYMENT & MAINTENANCE

### Goal
The system runs somewhere real, is observable, and has a plan for what happens after launch — plus this is where your chosen original extension (from `architecture.md` Section 14, Phase 6) gets built.

### 6.1 Deployment to Staging & Production
- Dockerized services (frontend, backend, worker) per `architecture.md` Section 46.
- Environment-based configuration; `.env.example` provided, real secrets never committed.
- Separate staging and production environments — test deployment steps on staging first.
- CI/CD pipeline (`architecture.md` Section 47): lint → type check → unit tests → integration tests → build → security checks → deploy gate.

### 6.2 User Feedback & Monitoring
- Structured logging per `architecture.md` Section 37: request latency, retrieval latency, LLM latency, token usage, errors, query types.
- Basic alerting for processing job failure rates and API error rates.
- A simple, honest way to collect user feedback if this is ever used by real testers (even just a feedback form) — not required for a solo resume project, but worth designing for.

### 6.3 Bug Fixes & Improvements
- Ongoing triage of the Known Issues log (`memory.md` Section 12).
- Regression tests added for every fixed bug so it can't silently reappear.

### 6.4 Future Enhancements (do NOT build all of these — this is a backlog, not a to-do list)
- Additional document format support (DOCX, URLs, Git repos) — per `architecture.md` Section 8.
- OAuth login providers.
- Date-based/temporal reasoning queries ("what changed in Q3 2025") — one of the candidate Phase 6 extensions from `architecture.md`.
- Applying VersionRAG's approach to a new document domain (legal/policy documents) — explicitly untested in the original research paper.
- Improved implicit/silent change detection beyond the original paper's 60% baseline.

### Phase 6 Definition of Done
- [ ] Application is deployed and reachable in a staging (minimum) or production environment
- [ ] Logging and basic monitoring are in place
- [ ] CI/CD pipeline runs on every change
- [ ] Exactly ONE original extension from Section 6.4 is fully built and benchmarked (not multiple half-built ones)
- [ ] `memory.md` fully updated, including final honest benchmark results and a clear "what's next" list

---

## How These Phases Relate to Your Other Documents

| File | Role |
|---|---|
| `architecture.md` | The **how** — system design, data model, pipelines |
| `design.md` | The **look and feel** — UI/UX specification |
| `memory.md` | The **what's actually happened** — real project state, updated every session |
| `phases.md` (this file) | The **order** — what gets built when, and what "done" means at each step |

**Golden rule for using this file:** do not start Phase N+1 until Phase N's Definition of Done checklist is genuinely checked off — not "mostly done," not "I'll finish testing later." This is exactly the discipline that separates a real production build from a project that quietly falls apart the moment an interviewer asks "what happens when X fails?"
