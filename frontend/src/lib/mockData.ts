import {
  User, Workspace, Project, Document, DocumentVersion,
  DocumentChange, VersionComparison, QueryResponse, EvaluationRun
} from '../types';

export const DEMO_USER: User = {
  id: '6c51f02b-f2e2-4acd-af64-7e77e8a1abad',
  email: 'demo@versionrag.dev',
  full_name: 'Alex Mercer (Staff Architect)',
  is_active: true,
  is_verified: true,
  is_superuser: true,
  created_at: '2026-08-26T15:45:54.040628',
};

export const DEMO_WORKSPACES: Workspace[] = [
  {
    id: '0e463f60-3625-4b87-ba2b-f6cebb2f60d3',
    name: 'Core Platform Engineering',
    slug: 'core-engineering',
    description: 'Production API & Documentation Knowledge Base with AST-Aware Semantic Partitioning',
    created_at: '2026-08-26T15:45:54.040628',
    current_user_role: 'owner',
    members_count: 12,
    projects_count: 1,
  },
];

export const DEMO_PROJECTS: Project[] = [
  {
    id: '7c7018d2-09ed-4431-ade9-ff4f52577c22',
    workspace_id: '0e463f60-3625-4b87-ba2b-f6cebb2f60d3',
    name: 'Node.js Runtime & API Specifications',
    slug: 'nodejs-runtime-specs',
    description: 'Version-aware documentation and migration tracks for Node.js assert & HTTP runtime modules.',
    created_at: '2026-08-26T15:45:54.040628',
    documents_count: 1,
    versions_count: 3,
    changes_count: 4,
  },
];

const V14: DocumentVersion = {
  id: 'v14-uuid',
  document_id: 'c1d924a8-c5d9-47b7-9c84-50e039240d6d',
  version_tag: 'v14.0.0',
  normalized_version: '14.0.0',
  version_order: 1,
  source_filename: 'assert_v14.md',
  file_size_bytes: 4280,
  mime_type: 'text/markdown',
  status: 'ready',
  chunks_count: 12,
  created_at: '2026-08-26T15:45:54.040628',
};

const V15: DocumentVersion = {
  id: 'v15-uuid',
  document_id: 'c1d924a8-c5d9-47b7-9c84-50e039240d6d',
  version_tag: 'v15.14.0',
  normalized_version: '15.14.0',
  version_order: 2,
  source_filename: 'assert_v15.md',
  file_size_bytes: 5120,
  mime_type: 'text/markdown',
  status: 'ready',
  chunks_count: 15,
  created_at: '2026-08-26T15:45:54.040628',
};

const V16: DocumentVersion = {
  id: 'v16-uuid',
  document_id: 'c1d924a8-c5d9-47b7-9c84-50e039240d6d',
  version_tag: 'v16.0.0',
  normalized_version: '16.0.0',
  version_order: 3,
  source_filename: 'assert_v16.md',
  file_size_bytes: 5890,
  mime_type: 'text/markdown',
  status: 'ready',
  chunks_count: 18,
  created_at: '2026-08-26T15:45:54.040628',
};

export const DEMO_DOCUMENTS: Document[] = [
  {
    id: 'c1d924a8-c5d9-47b7-9c84-50e039240d6d',
    project_id: '7c7018d2-09ed-4431-ade9-ff4f52577c22',
    family_id: 'fam-assert',
    title: 'Node.js Assert Documentation',
    doc_type: 'technical_documentation',
    source_url: 'https://nodejs.org/api/assert.html',
    description: 'Evolving assertion specifications across Node.js runtime versions.',
    created_at: '2026-08-26T15:45:54.040628',
    versions: [V14, V15, V16],
    latest_version: 'v16.0.0',
    total_versions: 3,
    status: 'ready',
  },
];

export const DEMO_CHANGES: DocumentChange[] = [
  {
    id: 'chg-1',
    document_id: 'c1d924a8-c5d9-47b7-9c84-50e039240d6d',
    from_version_id: 'v14-uuid',
    to_version_id: 'v15-uuid',
    from_version_tag: 'v14.0.0',
    to_version_tag: 'v15.14.0',
    location: 'assert.deepEqual(actual, expected)',
    change_type: 'breaking',
    severity: 'critical',
    is_silent: true,
    is_breaking: true,
    summary: 'Silent prototype comparison enforcement: assert.deepEqual now strictly compares Object prototypes instead of using Abstract Equality (==).',
    old_content: 'assert.deepEqual(actual, expected[, message])\nPrimitive values compared using ==. Object wrappers compared as primitive values.',
    new_content: 'assert.deepEqual(actual, expected[, message])\nPrototypes of objects are strictly compared. If prototypes differ, throws AssertionError.',
    confidence: 0.98,
    source: 'ast_analyzer',
    created_at: '2026-08-26T15:45:54.040628',
  },
  {
    id: 'chg-2',
    document_id: 'c1d924a8-c5d9-47b7-9c84-50e039240d6d',
    from_version_id: 'v14-uuid',
    to_version_id: 'v15-uuid',
    from_version_tag: 'v14.0.0',
    to_version_tag: 'v15.14.0',
    location: 'assert.CallTracker',
    change_type: 'deprecated',
    severity: 'medium',
    is_silent: false,
    is_breaking: false,
    summary: 'assert.CallTracker is deprecated in favor of diagnostics_channel. Scheduled for removal in v16.0.0.',
    confidence: 0.95,
    source: 'changelog_extractor',
    created_at: '2026-08-26T15:45:54.040628',
  },
  {
    id: 'chg-3',
    document_id: 'c1d924a8-c5d9-47b7-9c84-50e039240d6d',
    from_version_id: 'v15-uuid',
    to_version_id: 'v16-uuid',
    from_version_tag: 'v15.14.0',
    to_version_tag: 'v16.0.0',
    location: 'assert.CallTracker',
    change_type: 'removed',
    severity: 'high',
    is_silent: false,
    is_breaking: true,
    summary: 'assert.CallTracker completely removed from runtime export table.',
    confidence: 1.0,
    source: 'ast_analyzer',
    created_at: '2026-08-26T15:45:54.040628',
  },
  {
    id: 'chg-4',
    document_id: 'c1d924a8-c5d9-47b7-9c84-50e039240d6d',
    from_version_id: 'v15-uuid',
    to_version_id: 'v16-uuid',
    from_version_tag: 'v15.14.0',
    to_version_tag: 'v16.0.0',
    location: 'AssertionError.cause',
    change_type: 'added',
    severity: 'low',
    is_silent: false,
    is_breaking: false,
    summary: 'Introduced error cause chaining across all assertion failures via .cause attribute.',
    confidence: 0.99,
    source: 'ast_analyzer',
    created_at: '2026-08-26T15:45:54.040628',
  },
];

export const DEMO_EVALUATIONS: EvaluationRun[] = [
  {
    id: 'eval-demo-run',
    workspace_id: '0e463f60-3625-4b87-ba2b-f6cebb2f60d3',
    project_id: '7c7018d2-09ed-4431-ade9-ff4f52577c22',
    name: 'Auto-RAGAS Triple-Baseline Evaluation Suite',
    dataset_name: 'nodejs-assert-version-drift-benchmark',
    status: 'completed',
    naive_rag_accuracy: 0.417,
    version_aware_accuracy: 0.782,
    versionrag_accuracy: 0.984,
    naive_rag_faithfulness: 0.521,
    versionrag_faithfulness: 0.992,
    retrieval_precision: 0.984,
    retrieval_recall: 0.967,
    cross_version_contamination_rate: 0.0,
    silent_change_detection_rate: 0.942,
    average_latency_ms: 5.4,
    total_scenarios: 30,
    passed_scenarios: 30,
    summary_report: {
      total_runs: 30,
      contamination_eliminated: '100% (down from 62.5% to 0.0%)',
      precision_at_6_lift: '+136.0% (41.7% -> 98.4%)',
      silent_change_recall: '94.2%',
      latency_p95_ms: 6.8,
    },
    metrics_definitions: {
      accuracy: {
        name: 'Top-1 Version Accuracy',
        formula: 'Correctly resolved versioned assertions / Total queries',
        description: 'Percentage of questions where the retrieved answer corresponds strictly to the queried API version.',
      },
      contamination: {
        name: 'Cross-Version Contamination Rate',
        formula: 'Contaminated retrieved chunks / Total retrieved chunks',
        description: 'Rate at which chunks from non-targeted API versions bleed into LLM context.',
      },
    },
    created_at: '2026-08-26T15:45:54.040628',
    results: [
      {
        id: 'scen-1',
        query_archetype: 'breaking_behavioral_drift',
        question: 'Does assert.deepEqual check prototypes strictly in Node v14?',
        target_version: 'v14.0.0',
        ground_truth_answer: 'No, in Node v14 assert.deepEqual uses abstract equality (==) for primitives and does NOT strictly compare prototypes.',
        naive_rag_answer: 'Yes, assert.deepEqual throws AssertionError if object prototypes differ.',
        naive_rag_correct: 0,
        versionrag_answer: 'No, in Node.js v14.0.0, assert.deepEqual does not compare prototypes strictly; primitive values are compared with Abstract Equality (==). Prototype strictness was introduced in v15.14.0.',
        versionrag_correct: 1,
        versionrag_confidence: 'high',
        retrieved_versions: ['v14.0.0'],
        evidence_valid: 1,
        execution_time_ms: 4.8,
      },
      {
        id: 'scen-2',
        query_archetype: 'silent_deprecation',
        question: 'Can I use assert.CallTracker in Node v16?',
        target_version: 'v16.0.0',
        ground_truth_answer: 'No, assert.CallTracker was removed in Node.js v16.0.0. Use diagnostics_channel instead.',
        naive_rag_answer: 'assert.CallTracker is available to track function call counts.',
        naive_rag_correct: 0,
        versionrag_answer: 'No, assert.CallTracker was completely removed in Node.js v16.0.0. It was deprecated in v15.14.0 in favor of diagnostics_channel.',
        versionrag_correct: 1,
        versionrag_confidence: 'high',
        retrieved_versions: ['v16.0.0'],
        evidence_valid: 1,
        execution_time_ms: 5.2,
      },
    ],
  },
];

export const DEMO_COMPARISON: VersionComparison = {
  document_id: 'c1d924a8-c5d9-47b7-9c84-50e039240d6d',
  from_version_tag: 'v14.0.0',
  to_version_tag: 'v15.14.0',
  summary: {
    breaking: 1,
    deprecated: 1,
    added: 1,
    total: 3,
  },
  changes: DEMO_CHANGES.slice(0, 2),
  unified_diff: `--- assert_v14.md (v14.0.0)
+++ assert_v15.md (v15.14.0)
@@ -10,6 +10,8 @@
-### assert.deepEqual(actual, expected[, message])
-Tests for deep equality between the actual and expected parameters.
-Primitive values are compared with the Abstract Equality Comparison (==).
+### assert.deepEqual(actual, expected[, message])
+Tests for deep equality between the actual and expected parameters.
+Prototypes of objects are strictly compared. If prototypes differ, throws AssertionError.
+
+### assert.CallTracker
+[DEPRECATED] Tracks function call counts for unit testing.`,
};

export const DEMO_QUERY_RESPONSE: QueryResponse = {
  conversation_id: 'conv-demo-1',
  message_id: 'msg-demo-1',
  question: 'How does assert.deepEqual compare object prototypes across v14 and v15?',
  answer: 'In **Node.js v14.0.0**, `assert.deepEqual()` compares primitive values using Abstract Equality (`==`) and does **not** compare prototypes strictly. In **v15.14.0**, this behavior underwent a **silent breaking change**: prototypes of objects are now strictly validated, and mismatched prototypes immediately trigger an `AssertionError`.',
  query_type: 'version_comparative',
  target_version: 'v15.14.0',
  related_versions: ['v14.0.0', 'v15.14.0'],
  confidence_level: 'high',
  confidence_score: 0.98,
  confidence_reason: 'Resolved via SQL Hard Version Partition Gate + Okapi BM25 & pgvector HNSW Reciprocal Rank Fusion (k=60).',
  has_conflict: true,
  conflict_summary: 'Behavioral collision detected between v14.0.0 (abstract equality) and v15.14.0 (strict prototype checking).',
  compatibility_matrix: [
    {
      version_tag: 'v14.0.0',
      symbol: 'assert.deepEqual',
      status: 'permissive_prototype',
      is_breaking: false,
      is_silent: false,
      behavior_summary: 'Abstract equality (==); prototypes are not checked.',
    },
    {
      version_tag: 'v15.14.0',
      symbol: 'assert.deepEqual',
      status: 'strict_prototype',
      is_breaking: true,
      is_silent: true,
      behavior_summary: 'Object prototypes must strictly match; throws AssertionError on mismatch.',
    },
  ],
  is_invariant: false,
  citations: [
    {
      id: 'cit-1',
      document_title: 'Node.js Assert Documentation',
      version_tag: 'v15.14.0',
      section_title: 'assert.deepEqual(actual, expected[, message])',
      page_number: 1,
      snippet: 'Prototypes of objects are strictly compared. If prototypes differ, assert.deepEqual() throws an AssertionError.',
      similarity_score: 0.984,
      citation_order: 1,
      retrieval_telemetry: {
        engine: 'VersionRAG Hybrid RRF (k=60)',
        partition_gate: 'WHERE version_id = v15.14.0',
        dense_score: 0.942,
        bm25_score: 18.64,
        rrf_score: 0.0328,
        cross_encoder_score: 0.984,
        dense_rank: 1,
        bm25_rank: 1,
        symbol_boost: 0.15,
        ast_symbol_matched: 'assert.deepEqual',
        final_score: 0.984,
      },
    },
    {
      id: 'cit-2',
      document_title: 'Node.js Assert Documentation',
      version_tag: 'v14.0.0',
      section_title: 'assert.deepEqual(actual, expected[, message])',
      page_number: 1,
      snippet: 'Primitive values are compared with the Abstract Equality Comparison (==). Object wrappers are compared as their primitive values.',
      similarity_score: 0.912,
      citation_order: 2,
      retrieval_telemetry: {
        engine: 'VersionRAG Hybrid RRF (k=60)',
        partition_gate: 'WHERE version_id = v14.0.0',
        dense_score: 0.891,
        bm25_score: 16.12,
        rrf_score: 0.0294,
        cross_encoder_score: 0.912,
        dense_rank: 2,
        bm25_rank: 2,
        symbol_boost: 0.10,
        ast_symbol_matched: 'assert.deepEqual',
        final_score: 0.912,
      },
    },
  ],
  latency_ms: 5.4,
  tokens_used: 312,
};

export const DEMO_MIGRATION_GUIDE = {
  from_tag: 'v14.0.0',
  to_tag: 'v15.14.0',
  risk_score: 'HIGH',
  risk_color: 'amber',
  breaking_count: 1,
  deprecated_count: 1,
  added_count: 1,
  steps: [
    {
      step: 1,
      title: 'Audit Prototype Strictness in assert.deepEqual',
      severity: 'critical',
      description: 'Replace loose object literal assertions where prototype differences exist with explicit assert.strictEqual or prototype normalization.',
      code_before: 'assert.deepEqual(Object.create({ a: 1 }), { a: 1 }); // Passes in v14',
      code_after: 'assert.deepStrictEqual(Object.create({ a: 1 }), { a: 1 }); // Throws in v15: normalize prototypes first',
    },
    {
      step: 2,
      title: 'Migrate from assert.CallTracker to diagnostics_channel',
      severity: 'medium',
      description: 'assert.CallTracker is deprecated in v15 and removed in v16. Refactor tracking logic to Node diagnostic channels.',
      code_before: 'const tracker = new assert.CallTracker();',
      code_after: 'import diagnostics_channel from "diagnostics_channel";',
    },
  ],
  markdown_guide: '# Automated Migration Playbook: Node.js Assert v14.0.0 -> v15.14.0\n\n## Summary\nDetected 1 silent breaking change in `assert.deepEqual` and 1 deprecation in `assert.CallTracker`.\n\n## Action Items\n1. Normalize object prototypes prior to deep equality assertion.\n2. Replace CallTracker with diagnostics_channel.',
};

export const DEMO_CODE_SCAN = {
  from_tag: 'v14.0.0',
  to_tag: 'v15.14.0',
  risk_level: 'HIGH',
  compatibility_score: 66.7,
  summary_counts: {
    total_lines_scanned: 15,
    vulnerable_lines: 2,
    breaking_lines: 1,
    silent_lines: 1,
    deprecated_lines: 1,
  },
  line_findings: [
    {
      line_number: 4,
      original_line: 'assert.deepEqual(result, Object.create(expected));',
      refactored_line: 'assert.deepStrictEqual(Object.assign({}, result), Object.assign({}, expected));',
      symbol: 'assert.deepEqual',
      change_type: 'breaking',
      severity: 'critical',
      is_breaking: true,
      is_silent: true,
      issue_summary: 'Strict prototype validation will fail due to Object.create prototype inheritance difference.',
      fix_explanation: 'Flatten objects using Object.assign or ensure prototype matching before assertion.',
      citation: {
        version_tag: 'v15.14.0',
        section: 'assert.deepEqual',
        excerpt: 'Prototypes of objects are strictly compared.',
      },
    },
    {
      line_number: 8,
      original_line: 'const tracker = new assert.CallTracker();',
      refactored_line: 'const channel = diagnostics_channel.channel("test_calls");',
      symbol: 'assert.CallTracker',
      change_type: 'deprecated',
      severity: 'medium',
      is_breaking: false,
      is_silent: false,
      issue_summary: 'assert.CallTracker deprecated in v15.14.0, will break on v16.',
      fix_explanation: 'Migrate to diagnostics_channel.',
      citation: {
        version_tag: 'v15.14.0',
        section: 'assert.CallTracker',
        excerpt: 'Deprecated in favor of diagnostics_channel.',
      },
    },
  ],
  original_code: `const assert = require('assert');

function runTest(result, expected) {
  assert.deepEqual(result, Object.create(expected));
}

function trackCalls() {
  const tracker = new assert.CallTracker();
}`,
  refactored_code: `const assert = require('assert');
const diagnostics_channel = require('diagnostics_channel');

function runTest(result, expected) {
  assert.deepStrictEqual(Object.assign({}, result), Object.assign({}, expected));
}

function trackCalls() {
  const channel = diagnostics_channel.channel("test_calls");
}`,
  unified_diff: `--- original_service.js
+++ refactored_service.js
@@ -1,8 +1,9 @@
 const assert = require('assert');
+const diagnostics_channel = require('diagnostics_channel');
 
 function runTest(result, expected) {
-  assert.deepEqual(result, Object.create(expected));
+  assert.deepStrictEqual(Object.assign({}, result), Object.assign({}, expected));
 }
 
 function trackCalls() {
-  const tracker = new assert.CallTracker();
+  const channel = diagnostics_channel.channel("test_calls");
 }`,
};

export const DEMO_LLM_CONFIG = {
  active_provider: 'local_deterministic',
  active_model: 'VersionRAG-v1-Deterministic',
  has_api_key: true,
  masked_api_key: 'sk-proj-****LOCAL****',
  configured_providers: ['local_deterministic', 'openai', 'gemini'],
  supported_providers: [
    {
      id: 'local_deterministic',
      name: 'Deterministic Offline Engine',
      default_model: 'VersionRAG-v1-Deterministic',
      requires_key: false,
      badge: 'Zero API Key Required',
    },
    {
      id: 'openai',
      name: 'OpenAI GPT-4o',
      default_model: 'gpt-4o-mini',
      requires_key: true,
      badge: 'Cloud LLM',
    },
    {
      id: 'gemini',
      name: 'Google Gemini 2.5 Flash',
      default_model: 'gemini-1.5-flash',
      requires_key: true,
      badge: 'Cloud LLM',
    },
  ],
};

export const DEMO_AUTO_SCENARIOS = {
  project_id: '7c7018d2-09ed-4431-ade9-ff4f52577c22',
  total_synthesized: 2,
  scenarios: [
    {
      query_archetype: 'breaking_behavioral_drift',
      question: 'Does assert.deepEqual check prototypes strictly in Node v14?',
      target_version: 'v14.0.0',
      ground_truth_answer: 'No, in Node v14 assert.deepEqual uses abstract equality (==) and does NOT strictly compare prototypes.',
      target_keywords: ['assert.deepEqual', 'prototype', 'v14'],
      failure_taxonomy: 'Cross-version contamination from v15.14.0 where prototypes became strict.',
      explanation: 'Verifies whether the hybrid retrieval engine rejects v15 prototype docs when querying v14.',
    },
  ],
};

