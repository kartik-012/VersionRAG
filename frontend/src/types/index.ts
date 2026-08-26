export type WorkspaceRole = 'owner' | 'admin' | 'member' | 'viewer';

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  description?: string;
  created_at: string;
  current_user_role?: WorkspaceRole;
  members_count?: number;
  projects_count?: number;
}

export interface Project {
  id: string;
  workspace_id: string;
  name: string;
  slug: string;
  description?: string;
  created_at: string;
  documents_count?: number;
  versions_count?: number;
  changes_count?: number;
}

export interface DocumentVersion {
  id: string;
  document_id: string;
  version_tag: string;
  normalized_version?: string;
  version_order: number;
  source_filename?: string;
  file_size_bytes: number;
  mime_type?: string;
  status: 'pending' | 'processing' | 'ready' | 'needs_review' | 'failed';
  status_message?: string;
  previous_version_id?: string;
  next_version_id?: string;
  extracted_metadata?: Record<string, any>;
  change_summary?: Record<string, number>;
  raw_content?: string;
  created_at: string;
  chunks_count?: number;
}

export interface Document {
  id: string;
  project_id: string;
  family_id?: string;
  title: string;
  doc_type: string;
  source_url?: string;
  description?: string;
  created_at: string;
  versions: DocumentVersion[];
  latest_version?: string;
  total_versions: number;
  status?: string;
}

export type ChangeType =
  | 'added'
  | 'removed'
  | 'modified'
  | 'renamed'
  | 'deprecated'
  | 'restored'
  | 'behavioral'
  | 'breaking'
  | 'doc_only'
  | 'silent';

export type ChangeSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface DocumentChange {
  id: string;
  document_id: string;
  from_version_id: string;
  to_version_id: string;
  from_version_tag: string;
  to_version_tag: string;
  location: string;
  change_type: ChangeType;
  severity: ChangeSeverity;
  is_silent: boolean;
  is_breaking: boolean;
  old_content?: string;
  new_content?: string;
  summary: string;
  confidence: number;
  source: string;
  details?: Record<string, any>;
  created_at: string;
}

export interface VersionComparison {
  document_id: string;
  from_version_tag: string;
  to_version_tag: string;
  summary: Record<string, number>;
  changes: DocumentChange[];
  unified_diff?: string;
}

export interface Citation {
  id: string;
  chunk_id?: string;
  document_title: string;
  version_tag: string;
  section_title?: string;
  page_number: number;
  snippet: string;
  similarity_score: number;
  citation_order: number;
}

export interface QueryResponse {
  conversation_id: string;
  message_id: string;
  question: string;
  answer: string;
  query_type: string;
  target_version?: string;
  related_versions: string[];
  confidence_level: 'high' | 'moderate' | 'low' | 'insufficient_evidence';
  confidence_score: number;
  confidence_reason: string;
  has_conflict: boolean;
  conflict_summary?: string;
  citations: Citation[];
  latency_ms: number;
  tokens_used: number;
}

export interface ProcessingJob {
  id: string;
  workspace_id: string;
  project_id: string;
  document_id?: string;
  version_id?: string;
  job_type: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  current_stage: string;
  stage_progress: number;
  error_message?: string;
  retry_count: number;
  created_at: string;
}

export interface EvaluationScenarioResult {
  id: string;
  query_archetype: string;
  question: string;
  target_version?: string;
  ground_truth_answer: string;
  naive_rag_answer?: string;
  naive_rag_correct: number;
  versionrag_answer: string;
  versionrag_correct: number;
  versionrag_confidence: string;
  retrieved_versions: string[];
  evidence_valid: number;
  execution_time_ms: number;
  failure_cause?: string;
  retrieved_chunks_naive?: Array<{
    chunk_id: string;
    version_tag: string;
    similarity_score: number;
    section_title?: string;
    snippet: string;
    is_contamination: boolean;
  }>;
  retrieved_chunks_versionrag?: Array<{
    chunk_id: string;
    version_tag: string;
    similarity_score: number;
    section_title?: string;
    snippet: string;
    is_contamination: boolean;
  }>;
  metrics_trace?: Record<string, any>;
}

export interface EvaluationRun {
  id: string;
  workspace_id: string;
  project_id: string;
  name: string;
  dataset_name: string;
  status: string;
  naive_rag_accuracy: number;
  version_aware_accuracy: number;
  versionrag_accuracy: number;
  naive_rag_faithfulness: number;
  versionrag_faithfulness: number;
  retrieval_precision: number;
  retrieval_recall: number;
  cross_version_contamination_rate?: number;
  silent_change_detection_rate: number;
  average_latency_ms: number;
  total_scenarios: number;
  passed_scenarios: number;
  summary_report: Record<string, any>;
  metrics_definitions?: Record<string, {
    name: string;
    formula: string;
    description: string;
  }>;
  created_at: string;
  results: EvaluationScenarioResult[];
}
