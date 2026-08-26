# VERSIONRAG — PRODUCTION WEB APPLICATION
## Master Product Requirements & Engineering Prompt

You are the **entire senior product engineering team** responsible for designing and building VersionRAG.

Act as:

- Principal Software Architect
- Senior AI/ML Engineer
- Senior Backend Engineer
- Senior Frontend Engineer
- Database Architect
- DevOps/SRE Engineer
- Security Engineer
- Product Designer
- QA Engineer
- Technical Product Manager

Build this as a **REAL WEB APPLICATION intended for real users**, not a portfolio project, college project, mockup, prototype, or resume demonstration.

Do NOT optimize for resume bullets or visual gimmicks.

Optimize for:

**Correctness → User value → Reliability → Security → Performance → Scalability → Maintainability → Excellent UX**

---

# 1. PRODUCT

## Product Name

**VersionRAG**

## Product Description

VersionRAG is a version-aware Retrieval-Augmented Generation platform for understanding documents that evolve over time.

Users can upload multiple versions of documents and ask questions that require the system to understand:

- which version is relevant
- what changed between versions
- when a change occurred
- whether information conflicts between versions
- what the source evidence says
- how confident the system is in its answer

The system must prevent the major problem of conventional RAG:

> Mixing information from incompatible document versions and generating an answer that is factually plausible but historically/version-wise incorrect.

---

# 2. REAL USER PROBLEM

Real organizations maintain evolving documents such as:

- API documentation
- Software documentation
- Product specifications
- Internal company policies
- Compliance documents
- Legal documents
- Technical standards
- Research documentation
- Release documentation
- Configuration documentation

Example:

A company has:

Version 14
Version 15
Version 16

of an API specification.

A user asks:

> "Was feature X supported in version 15?"

A conventional RAG system may retrieve:

- evidence from v14
- evidence from v15
- evidence from v16

and combine them.

VersionRAG must instead understand the question's version context and retrieve appropriate evidence.

---

# 3. PRIMARY USER

The first version should target users who work with evolving technical documentation.

Primary users:

- Software engineers
- Developers
- Technical documentation teams
- DevOps engineers
- API consumers
- Engineering teams
- Technical support teams

The architecture should remain extensible to other document domains later.

---

# 4. CORE USER JOURNEY

The complete user journey should be:

```text
Sign Up
   ↓
Create Workspace
   ↓
Create Project
   ↓
Upload Documents
   ↓
Version Detection
   ↓
Document Processing
   ↓
Version Organization
   ↓
Change Detection
   ↓
Indexing
   ↓
Ready
   ↓
Ask Questions
   ↓
Version-Aware Retrieval
   ↓
Evidence Selection
   ↓
Answer Generation
   ↓
Citation + Confidence
```

The experience must feel like a real SaaS product.

---

# 5. AUTHENTICATION

Implement proper authentication.

Requirements:

- Sign up
- Login
- Logout
- Password reset
- Session management
- Email verification where appropriate
- Protected routes
- Secure cookies/tokens
- User profile
- Workspace membership

Do not build fake authentication.

Design the authentication architecture so OAuth providers can be added later.

---

# 6. WORKSPACES

Users should not simply upload documents into one global database.

Create:

```text
User
 └── Workspace
      └── Project
           └── Documents
                └── Versions
```

A workspace represents an organization/team.

Requirements:

- Create workspace
- Rename workspace
- Delete workspace
- Workspace members
- Roles
- Permissions
- Workspace isolation

Possible roles:

- Owner
- Admin
- Member
- Viewer

Every request must enforce workspace-level authorization.

---

# 7. PROJECTS

A workspace can contain multiple VersionRAG projects.

Example:

```text
Acme Corporation

Projects

├── Public API Documentation
├── Internal Engineering Docs
├── Mobile SDK
└── Cloud Platform
```

Each project should have its own:

- documents
- versions
- indexes
- change history
- conversations
- settings
- analytics

---

# 8. DOCUMENT INGESTION

Support the following initially:

- PDF
- Markdown
- TXT
- HTML

Architecture should allow future support for:

- DOCX
- URLs
- Git repositories
- documentation websites
- API specifications

Upload flow:

```text
Upload
 ↓
Validate
 ↓
Store original
 ↓
Parse
 ↓
Clean
 ↓
Extract metadata
 ↓
Identify version
 ↓
Identify document family
 ↓
Chunk
 ↓
Embed
 ↓
Index
 ↓
Compare with previous versions
 ↓
Generate change information
 ↓
Ready
```

The original uploaded file must remain accessible.

---

# 9. DOCUMENT METADATA

Automatically extract:

- title
- version
- document type
- release date
- author/organization when available
- source URL when available
- document family
- detected language
- processing status

Do not trust LLM extraction blindly.

Store:

```text
detected_value
confidence
source
```

If version information cannot be confidently determined, tell the user.

Do not silently invent a version.

---

# 10. VERSION MANAGEMENT

Version information must be a first-class concept.

Support:

```text
1.0
1.1
1.2
2.0

v14
v15
v16

2025.01
2025.02

2025-Q1
2025-Q2
```

Do not assume every document follows Semantic Versioning.

Each version should contain:

- version identifier
- release date
- source document
- parent/previous version
- processing status
- created timestamp
- metadata
- change summary

---

# 11. DOCUMENT FAMILY DETECTION

The system should determine whether uploaded documents belong to the same evolving document.

Example:

```text
Node.js Assert API v14
Node.js Assert API v15
Node.js Assert API v16
```

→ Same document family.

But:

```text
Node.js Assert API
Node.js HTTP API
```

→ Different document families.

Use multiple signals:

- title
- metadata
- URL
- semantic similarity
- structure
- version information

Allow users to manually correct the detected relationship.

---

# 12. DOCUMENT PROCESSING

Processing must be asynchronous.

Do not make the browser wait for an entire ingestion pipeline.

Use background workers.

Example:

```text
Upload API
   ↓
Job Queue
   ↓
Worker
   ├── Parse
   ├── Metadata extraction
   ├── Chunking
   ├── Embedding
   ├── Change detection
   └── Indexing
```

The UI must display processing status:

```text
Uploading
Processing
Extracting metadata
Creating embeddings
Comparing versions
Indexing
Completed
Failed
```

Users should be able to retry failed processing jobs.

---

# 13. CHUNKING

Implement intelligent chunking.

Default baseline:

- approximately 512 tokens
- approximately 50-token overlap

But do not blindly apply fixed chunking to every document.

Where appropriate, preserve:

- headings
- sections
- paragraphs
- code blocks
- tables
- lists

Every chunk must retain metadata:

```text
workspace_id
project_id
document_id
version_id
chunk_id
section
page
source
version
```

---

# 14. VECTOR SEARCH

Each chunk must be version-aware.

Never store a vector without sufficient metadata to identify its source version.

Example:

```text
chunk_id
document_id
version_id
version
embedding
text
section
page
```

Implement metadata filtering.

A query targeting v15 must not accidentally retrieve v16 evidence unless the system explicitly determines that cross-version evidence is necessary.

---

# 15. RETRIEVAL ARCHITECTURE

Do not build a simple:

```text
Question → Vector Search → LLM
```

Instead:

```text
Question
 ↓
Query Understanding
 ↓
Version / Date / Intent Detection
 ↓
Retrieval Strategy Selection
 ↓
Candidate Retrieval
 ↓
Version Filtering
 ↓
Reranking
 ↓
Evidence Validation
 ↓
Context Assembly
 ↓
LLM
```

---

# 16. QUERY TYPES

The system should recognize at least:

### Type 1 — Content

> "How does function X work?"

### Type 2 — Version-specific

> "How does function X work in v15?"

### Type 3 — Version comparison

> "What changed between v14 and v15?"

### Type 4 — Change

> "When was function X deprecated?"

### Type 5 — Timeline

> "When did this behavior change?"

### Type 6 — Historical

> "What did the documentation say in 2023?"

### Type 7 — Conflict

> "Why does v15 say X while v16 says Y?"

### Type 8 — Silent change

> "Was this behavior changed without being mentioned in the changelog?"

The retrieval strategy must depend on query type.

---

# 17. VERSION-AWARE ANSWERING

This is the heart of VersionRAG.

Example:

User:

> Is feature X supported in v15?

The system should internally determine:

```text
Question
 ↓
Target version = v15
 ↓
Retrieve v15 evidence
 ↓
Check adjacent versions if useful
 ↓
Check change history
 ↓
Generate answer
```

It must NOT simply retrieve the most semantically similar chunks across all versions.

---

# 18. CHANGE DETECTION

Implement two approaches.

## Explicit Change Detection

Use available:

- changelogs
- release notes
- migration guides
- deprecation notices

## Implicit Change Detection

Compare actual content between versions.

Use an appropriate diff system such as DeepDiff where structurally applicable.

The raw diff should then be converted into a structured human-readable change.

Example:

```text
Version 14 → Version 15

Feature:
assert.deepEqual()

Change Type:
Behavioral Change

Previous:
...

New:
...

Summary:
...

Severity:
Medium

Confidence:
0.91
```

---

# 19. CHANGE TYPES

Support:

- Added
- Removed
- Modified
- Renamed
- Deprecated
- Restored
- Behavioral change
- Breaking change
- Documentation-only change

Each change should contain:

```text
change_id
old_version
new_version
location
change_type
old_content
new_content
summary
severity
confidence
source
```

---

# 20. VERSION TIMELINE

Provide a visual timeline.

Example:

```text
v14.0 ───── v14.5 ───── v15.0 ───── v15.2 ───── v16.0
   │           │            │            │            │
  12           5           23            7           14
 changes     changes      changes      changes      changes
```

Users should be able to click a version and inspect:

- document
- changes
- additions
- removals
- deprecated features
- breaking changes

---

# 21. VERSION COMPARISON

Users should be able to select:

```text
From: v14
To:   v15
```

and receive:

```text
Summary

Added:       12
Modified:     8
Removed:      3
Deprecated:   4
Breaking:     2
```

Then allow drilling into every change.

---

# 22. QUESTION ANSWERING UI

The primary interface should be a professional workspace rather than a generic chatbot.

Example:

```text
┌─────────────────────────────────────────────┐
│ Ask VersionRAG                              │
│                                             │
│ What changed in authentication between     │
│ v14 and v15?                                │
│                                      [Ask]  │
└─────────────────────────────────────────────┘
```

Answer:

```text
Answer

Authentication changed in v15 in two
important ways...

Relevant Version
v15

Evidence
──────────────
Source: Authentication.md
Version: v15
Section: OAuth

Confidence
92%

Changes considered
v14 → v15
```

---

# 23. EVIDENCE VIEWER

Users must be able to inspect why the system produced an answer.

For every answer show:

- source document
- version
- page/section
- relevant text
- retrieval score where useful
- citation
- change relationship

Clicking a citation should take the user directly to the relevant document context.

---

# 24. CONFLICT DETECTION

If retrieved evidence conflicts, do not hide it.

Example:

```text
⚠ Conflicting Evidence

v14:
Feature X is supported.

v15:
Feature X is deprecated.

v16:
Feature X is removed.

Timeline:
Supported → Deprecated → Removed
```

The system should explain the conflict using version ordering.

---

# 25. CONFIDENCE

Every answer should have a confidence indicator.

Do NOT simply ask an LLM:

> "How confident are you?"

Build confidence from measurable signals such as:

- retrieval quality
- evidence quantity
- version consistency
- source quality
- evidence agreement
- answer/evidence alignment
- change detection reliability

If confidence is low:

```text
Low confidence

I found insufficient evidence to determine
the answer reliably.
```

The system must prefer:

**"I don't have enough evidence."**

over hallucinating.

---

# 26. DATABASE ARCHITECTURE

Prefer a simple architecture that can scale.

Recommended starting architecture:

```text
PostgreSQL
   +
pgvector
   +
Redis
```

Do not introduce multiple databases simply because they are fashionable.

If a graph database is genuinely required later, demonstrate why.

The system should have a clean abstraction layer so storage technologies can be replaced.

---

# 27. CORE DATA MODEL

Design proper relational entities for:

```text
User
Workspace
WorkspaceMember
Project
Document
DocumentVersion
DocumentChunk
Change
Conversation
Message
Citation
ProcessingJob
Evaluation
Usage
```

Use:

- UUIDs
- foreign keys
- constraints
- indexes
- timestamps
- soft deletion where appropriate
- migrations

Enforce tenant isolation.

---

# 28. API

Build a clean backend API.

Example:

```text
POST   /api/v1/auth/...
GET    /api/v1/workspaces
POST   /api/v1/workspaces

GET    /api/v1/projects
POST   /api/v1/projects

GET    /api/v1/documents
POST   /api/v1/documents

GET    /api/v1/documents/{id}
DELETE /api/v1/documents/{id}

GET    /api/v1/documents/{id}/versions
POST   /api/v1/documents/{id}/versions

GET    /api/v1/versions/{id}/changes

POST   /api/v1/query
POST   /api/v1/compare

GET    /api/v1/timeline/{document_id}

GET    /api/v1/jobs/{id}

GET    /api/v1/health
```

Use:

- request validation
- typed schemas
- consistent error responses
- authentication
- authorization
- rate limiting
- API versioning

---

# 29. FRONTEND

Build a real modern SaaS interface.

Recommended:

**Next.js + TypeScript**

The design should be:

- professional
- minimal
- fast
- accessible
- responsive
- information-dense where appropriate
- easy to understand

Do not create unnecessary animations.

Core navigation:

```text
Dashboard

Projects
Documents
Versions
Changes
Ask
Timeline
Settings
```

---

# 30. DASHBOARD

Show:

```text
Projects
Documents
Versions
Changes detected
Processing jobs
Recent activity
```

Also show processing failures and warnings.

The dashboard should help the user understand the state of their knowledge base.

---

# 31. DOCUMENT PAGE

A document page should contain:

```text
Document Name

Versions
────────────────────────────

v16.0
v15.0
v14.0

Timeline

Changes

Ask Questions
```

Users can upload a new version from here.

---

# 32. VERSION PAGE

Show:

- version metadata
- release date
- source
- previous version
- next version
- changes
- document contents
- indexed status
- processing information

---

# 33. CHANGE EXPLORER

Provide filters:

```text
All
Added
Modified
Removed
Deprecated
Breaking
Silent
```

Users can search changes.

Allow:

```text
v14 → v15
```

comparison.

---

# 34. SEARCH

Provide global search.

Search across:

- documents
- versions
- changes

Results must clearly show version information.

Example:

```text
Authentication

v15
OAuth configuration changed...

v14
OAuth configuration...

v13
Legacy authentication...
```

---

# 35. CONVERSATIONS

Allow users to maintain conversations.

Every conversation belongs to a project.

Store:

- question
- answer
- citations
- version context
- timestamp

Users can return to previous questions.

---

# 36. SECURITY

Treat uploaded documents as potentially confidential.

Protect against:

- prompt injection
- malicious document content
- cross-tenant data leakage
- unauthorized document access
- unauthorized version access
- insecure file access
- API abuse
- credential leakage
- excessive resource consumption

Never expose another workspace's documents.

Never allow the LLM to override application authorization.

Authorization must happen at the application/data layer.

---

# 37. OBSERVABILITY

Implement structured logging.

Track:

- request latency
- retrieval latency
- LLM latency
- embedding latency
- processing failures
- token usage
- model usage
- query type
- retrieval results
- errors

Use tracing where appropriate.

The system should make debugging possible.

---

# 38. COST CONTROL

Do not call an expensive LLM unnecessarily.

Use:

- batching
- caching
- deduplication
- asynchronous processing
- appropriate model selection
- incremental indexing
- incremental change detection

When a new version is uploaded, do not reprocess unrelated historical versions unnecessarily.

---

# 39. INCREMENTAL PROCESSING

This is critical.

If a project contains:

```text
v1
v2
v3
v4
v5
```

and the user uploads:

```text
v6
```

the system should not blindly rebuild everything.

Prefer:

```text
v5 ↔ v6
```

for change detection.

Only re-index what actually requires reprocessing.

---

# 40. FAILURE HANDLING

Every background operation must be recoverable.

Examples:

- parser failure
- embedding failure
- LLM timeout
- malformed PDF
- missing version
- database failure
- duplicate upload
- invalid document
- rate limit
- partial processing

The user should see useful errors.

Never leave documents permanently stuck in:

```text
Processing...
```

without recovery.

---

# 41. TESTING

Build tests from the beginning.

Include:

### Unit tests

Metadata extraction
Version parsing
Chunking
Diff logic
Query classification

### Integration tests

Upload → processing → indexing

### Retrieval tests

Correct version retrieval

### Security tests

Cross-workspace access

### Regression tests

Previously correct questions must remain correct after changes.

### End-to-end tests

Real user workflows.

---

# 42. EVALUATION SYSTEM

Build evaluation into the actual application architecture.

Create a benchmark dataset containing:

- content questions
- version questions
- comparison questions
- change questions
- historical questions
- silent-change questions
- conflicting-version questions

Compare:

```text
Naive RAG
Version-aware RAG
VersionRAG
```

Measure:

- answer correctness
- version correctness
- retrieval precision
- retrieval recall
- faithfulness
- change detection accuracy
- silent-change detection
- latency
- token usage
- cost

Do not hard-code or fabricate benchmark results.

---

# 43. RESEARCH FOUNDATION

Use the 2025 VersionRAG research paper as the initial research foundation.

The reported baseline figures are references for reproduction/evaluation, not guaranteed results for this application.

The application should distinguish between:

```text
Published research result
vs.
Our experimentally measured result
```

Never present an unverified number as our performance.

---

# 44. PRODUCT EXTENSION

After the core product is reliable, implement one major differentiating capability.

Preferred direction:

## Temporal + Version-Aware Reasoning

Allow questions such as:

> What changed during Q3 2025?

> What was the behavior of feature X before it was deprecated?

> When did this behavior first appear?

> Show me the evolution of authentication from v12 to v16.

This turns VersionRAG from simple metadata-filtered RAG into a system capable of reasoning over document evolution.

---

# 45. PERFORMANCE REQUIREMENTS

Design for growth.

The architecture should be capable of scaling from:

```text
1 user
10 documents
100 chunks
```

to:

```text
many organizations
thousands of documents
millions of chunks
```

without requiring a complete rewrite.

Do not prematurely optimize.

But avoid architecture that makes future scaling impossible.

---

# 46. DEPLOYMENT

The application must be deployable as a real service.

Separate:

```text
Frontend
Backend API
Worker
Database
Vector storage
Redis
Object/file storage
```

Use Docker.

Use environment-based configuration.

Never commit:

- API keys
- passwords
- database credentials
- secrets

Provide:

```text
.env.example
Dockerfile
docker-compose.yml
migration setup
production configuration
```

---

# 47. CI/CD

Set up automated checks:

```text
Lint
Type checking
Unit tests
Integration tests
Build
Security checks
```

Deployment should happen only after required checks pass.

---

# 48. DESIGN PRINCIPLES

Follow these principles throughout development:

### Principle 1
Do not build features without a user reason.

### Principle 2
Do not use AI where deterministic logic is better.

### Principle 3
Do not use a database just because it is trendy.

### Principle 4
Never hide uncertainty.

### Principle 5
Never mix incompatible versions silently.

### Principle 6
Every important AI decision should be inspectable.

### Principle 7
Prefer incremental processing.

### Principle 8
Keep components replaceable.

### Principle 9
Security must be enforced outside the LLM.

### Principle 10
Correctness is more important than flashy UI.

---

# 49. DEVELOPMENT PROCESS

Do NOT generate the entire application in one giant step.

Work incrementally.

Before implementing each major subsystem:

1. Explain the architecture.
2. Define interfaces.
3. Define database changes.
4. Define API contracts.
5. Implement.
6. Test.
7. Verify.
8. Only then continue.

Never silently rewrite unrelated working components.

Do not introduce unnecessary dependencies.

Do not create duplicate implementations of the same functionality.

---

# 50. DEFINITION OF DONE

A feature is NOT complete merely because the code compiles.

A feature is complete only when:

- frontend works
- backend works
- database integration works
- validation exists
- error handling exists
- authorization exists where required
- tests exist
- loading states exist
- failure states exist
- logs exist where useful
- documentation exists
- production configuration is considered

---

# 51. FINAL PRODUCT

The finished VersionRAG application should allow a real user to:

```text
Create account
      ↓
Create workspace
      ↓
Create project
      ↓
Upload evolving documents
      ↓
Automatically identify versions
      ↓
Process documents
      ↓
Build version-aware index
      ↓
Detect changes
      ↓
Explore timeline
      ↓
Compare versions
      ↓
Ask questions
      ↓
Receive version-correct answers
      ↓
Inspect evidence
      ↓
Understand changes
      ↓
See confidence
```

The final product should feel like a **real software product**, not an AI demo.

---

# 52. FIRST IMPLEMENTATION STEP

Before writing application code:

1. Finalize the architecture.
2. Finalize the database schema.
3. Finalize the API boundaries.
4. Finalize the frontend information architecture.
5. Finalize the ingestion pipeline.
6. Finalize the retrieval pipeline.
7. Define the MVP.
8. Define acceptance criteria.
9. Define the initial evaluation dataset.
10. Identify technical risks.

Then begin implementation with:

## PHASE 1 — FOUNDATION

Build:

```text
Repository
Docker
PostgreSQL
Redis
Backend
Frontend
Authentication
Workspace
Project
Document upload
Object/file storage
Background job infrastructure
```

Do not implement advanced AI features before the foundation is stable.

After that:

## PHASE 2 — VERSION INTELLIGENCE

Implement:

```text
Metadata extraction
Version detection
Document family detection
Version management
Chunking
Embeddings
Vector search
Version filtering
```

Then:

## PHASE 3 — CHANGE INTELLIGENCE

Implement:

```text
Explicit change extraction
Implicit diff
LLM change summarization
Change database
Version comparison
Timeline
```

Then:

## PHASE 4 — VERSION-AWARE RAG

Implement:

```text
Query understanding
Query routing
Version-aware retrieval
Reranking
Evidence validation
Answer generation
Citations
Confidence
Conflict detection
```

Then:

## PHASE 5 — PRODUCTION HARDENING

Implement:

```text
Security
Authorization
Rate limiting
Observability
Caching
Error recovery
Testing
Performance optimization
CI/CD
Deployment
```

Then:

## PHASE 6 — ADVANCED TEMPORAL REASONING

Implement:

```text
Date-aware queries
Historical reasoning
Evolution analysis
Cross-version reasoning
Advanced change detection
```

---

# ABSOLUTE RULE

Do not treat VersionRAG as a "portfolio project."

Treat it as a **real product that has users, data, costs, security requirements, failures, maintenance requirements, and business consequences.**

If my proposed implementation is technically weak, say so.

If a simpler architecture is better, choose the simpler architecture.

If a feature is unnecessary, remove it.

If an AI call can be replaced with deterministic logic, prefer deterministic logic.

If a claim requires experimentation, build the experiment rather than making the claim.

If something cannot be reliably implemented yet, explicitly identify the limitation.

Build VersionRAG as if it will be used by real engineering teams tomorrow.