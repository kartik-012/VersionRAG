# Changelog

All notable changes to the **VersionRAG** enterprise platform are documented in this file.
The project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.3.0] - 2026-11-06

### Added
- **Ultra-Lightweight Liveness Probe (`/api/v1/health/ping`)**: High-performance HTTP 200 liveness check endpoint for Docker / Kubernetes container probes with zero database overhead.
- **Query String Sanitization**: Whitespace trimming, line normalization, and empty question rejection on `QueryRequest` schema.
- **Docker Healthcheck Coordination**: Added native Python healthcheck command and healthy container startup dependency in `docker-compose.yml`.
- **Query Studio Session Reset**: Added quick reset control (`RotateCcw`) to clear conversation history in AI Query Studio.
- **Tenant Boundary Security Policy**: Added live policy indicator and tenant partition verification badges to Workspace Settings view.

### Enhanced
- **Document Chunk Ingestion**: Hardened `ChunkingService` against null-byte characters and empty chunk insertion.
- **Multi-Tenant Isolation Assurance**: Added regression test asserting 404 security enforcement on cross-tenant project listings.
- **Benchmark Observability**: Documented latency targets and response timing metrics across API endpoints.

---

## [1.2.0] - 2026-10-25

### Added
- **Production Code Auditor CLI (`python -m app.cli_audit`)**: Automated CI/CD gate auditing production source code against indexed AST diff graphs with `--output` JSON and formatted terminal report generation.
- **Auto-RAGAS Benchmark Exporter**: Instant JSON and CSV export utilities for benchmark runs and scenario drift tables in the evaluation workbench.
- **AST Contract Invariants**: Added strict parameter constraint mutation analysis (`ParamASTNode.has_breaking_constraint_against`) and case-insensitive symbol lookup in `FunctionASTNode`.
- **System Telemetry & Health Metrics**: Added round-trip database ping latency tracking (`database_latency_ms`) and server uptime instrumentation in `/api/v1/health`.
- **Diff View Productivity**: One-click unified diff clipboard patch copier with visual notification state.
- **A11y Navigation Enhancements**: Added semantic ARIA roles, `aria-current`, and visible focus rings across the sidebar navigation matrix.
- **Production HTTP Security Headers**: Hardened FastAPI middleware with `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Referrer-Policy`.

### Optimized
- **RRF Rank Fusion Stability**: Enforced positive smoothing constant boundary guards (`safe_k = max(1, rrf_k)`) in `HybridIndexService` to prevent division-by-zero on customized rank configurations.
- **Sanitized Environment Template**: Completely overhauled `.env.example` with documented configurations for SQLite, PostgreSQL (`pgvector`), Redis sliding-window limiters, and zero-OTP setups.

---

## [1.1.0] - 2026-10-15

### Added
- **1-Click Turnkey Demo Login**: Instant one-click credentials injection (`demo@versionrag.dev`) for rapid evaluation without mandatory email OTP validation.
- **Polyglot AST & OpenAPI Parser Engine**: Structural AST parsing supporting Python `ast`, JavaScript/TypeScript API signatures, and OpenAPI 3.x / Swagger 2.0 schemas.
- **Live BYOK LLM Gateway**: Runtime provider switching between Gemini 2.0 Flash, OpenAI GPT-4o-mini, Groq, and Local Deterministic Engine.
- **Multi-Version Compatibility Matrix**: Dynamic version ambiguity resolver rendering symbol evolution across releases with lock-in controls.

---

## [1.0.0] - 2026-08-26

### Added
- **3-Stage Partitioned Hybrid Retrieval Engine**: Hard SQL version partition gate, parallel Okapi BM25 ($k_1=1.5, b=0.75$) + 256-dim pgvector HNSW dense cosine search, and Reciprocal Rank Fusion ($k=60$).
- **Distributed Redis ZSET Sliding-Window Rate Limiter**: Multi-tier login rate limiting with automatic in-memory fallback.
- **Interactive Version Comparison Studio**: Line-by-line unified diff and semantic change timeline viewer.
- **Executive Dashboard**: Real-time project overview, breaking change breakdown, and document ingestion workbench.
