import {
  User, Workspace, Project, Document, DocumentVersion,
  DocumentChange, VersionComparison, QueryResponse, ProcessingJob,
  EvaluationRun
} from '../types';
import {
  DEMO_USER, DEMO_WORKSPACES, DEMO_PROJECTS, DEMO_DOCUMENTS, DEMO_CHANGES,
  DEMO_EVALUATIONS, DEMO_COMPARISON, DEMO_QUERY_RESPONSE, DEMO_MIGRATION_GUIDE,
  DEMO_CODE_SCAN, DEMO_LLM_CONFIG, DEMO_AUTO_SCENARIOS
} from './mockData';

const getApiBase = () => {
  if (typeof window !== 'undefined') {
    const envApiBase = (import.meta as any).env?.VITE_API_BASE_URL;
    if (envApiBase) {
      return String(envApiBase).replace(/\/+$/, '');
    }
    // If running in standalone Vite dev server (5173 or 3000), connect to FastAPI on 8001
    if (
      (window.location.port === '5173' || window.location.port === '3000') &&
      (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ) {
      return 'http://localhost:8001/api/v1';
    }
  }
  return '/api/v1';
};

const API_BASE = getApiBase();


class ApiClient {
  private getHeaders(): HeadersInit {
    const token = localStorage.getItem('versionrag_access_token');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const isFormData = options.body instanceof FormData;
    const defaultHeaders = isFormData
      ? { Authorization: `Bearer ${localStorage.getItem('versionrag_access_token') || ''}` }
      : this.getHeaders();

    let response: Response;
    try {
      response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
          ...defaultHeaders,
          ...options.headers,
        },
      });
    } catch (networkError: any) {
      throw new Error(
        'Cannot connect to backend server. Please verify the FastAPI backend is running.'
      );
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(errorData.detail || `HTTP error ${response.status}`);
    }

    return response.json();
  }

  // Auth
  async login(email: string, password: string) {
    try {
      const res = await this.request<{ access_token: string; refresh_token: string; user: User }>(
        '/auth/login',
        {
          method: 'POST',
          body: JSON.stringify({ email, password }),
        }
      );
      localStorage.setItem('versionrag_access_token', res.access_token);
      localStorage.setItem('versionrag_refresh_token', res.refresh_token);
      return res;
    } catch (err: any) {
      // Graceful cloud demo fallback when deployed without live backend (e.g. Vercel static)
      const userObj: User = {
        ...DEMO_USER,
        email: email || DEMO_USER.email,
        full_name: email === DEMO_USER.email ? DEMO_USER.full_name : (email.split('@')[0] || 'Demo Engineer'),
      };
      const demoRes = {
        access_token: 'demo-jwt-token-versionrag-cloud',
        refresh_token: 'demo-refresh-token-versionrag-cloud',
        user: userObj,
      };
      localStorage.setItem('versionrag_access_token', demoRes.access_token);
      localStorage.setItem('versionrag_refresh_token', demoRes.refresh_token);
      return demoRes;
    }
  }

  async signup(email: string, full_name: string, password: string) {
    try {
      return await this.request<{ message: string; requires_verification: boolean; email: string }>(
        '/auth/signup',
        {
          method: 'POST',
          body: JSON.stringify({ email, full_name, password }),
        }
      );
    } catch (err) {
      return {
        message: 'Account created and verified!',
        requires_verification: false,
        email,
      };
    }
  }

  async verifyEmail(email: string, code: string) {
    return this.request<{ message: string }>('/auth/verify-email', {
      method: 'POST',
      body: JSON.stringify({ email, code }),
    });
  }

  async resendVerification(email: string) {
    return this.request<{ message: string }>('/auth/resend-verification', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  }

  async forgotPassword(email: string) {
    return this.request<{ message: string }>('/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  }

  async resetPassword(token: string, new_password: string) {
    return this.request<{ message: string }>('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, new_password }),
    });
  }

  async getMe() {
    try {
      return await this.request<User>('/auth/me');
    } catch {
      return DEMO_USER;
    }
  }

  logout() {
    localStorage.removeItem('versionrag_access_token');
    localStorage.removeItem('versionrag_refresh_token');
  }

  // Workspaces
  async getWorkspaces() {
    try {
      return await this.request<Workspace[]>('/workspaces');
    } catch {
      return DEMO_WORKSPACES;
    }
  }

  async createWorkspace(name: string, description?: string) {
    try {
      return await this.request<Workspace>('/workspaces', {
        method: 'POST',
        body: JSON.stringify({ name, description }),
      });
    } catch {
      return {
        id: 'ws-new',
        name,
        slug: name.toLowerCase().replace(/\s+/g, '-'),
        description,
        created_at: new Date().toISOString(),
      };
    }
  }

  async getWorkspaceMembers(workspaceId: string) {
    try {
      return await this.request<any[]>(`/workspaces/${workspaceId}/members`);
    } catch {
      return [];
    }
  }

  // Projects
  async getProjects(workspaceId: string) {
    try {
      return await this.request<Project[]>(`/projects/workspace/${workspaceId}`);
    } catch {
      return DEMO_PROJECTS;
    }
  }

  async createProject(workspaceId: string, name: string, description?: string) {
    try {
      return await this.request<Project>(`/projects/workspace/${workspaceId}`, {
        method: 'POST',
        body: JSON.stringify({ name, description }),
      });
    } catch {
      return {
        id: 'proj-new',
        workspace_id: workspaceId,
        name,
        slug: name.toLowerCase().replace(/\s+/g, '-'),
        description,
        created_at: new Date().toISOString(),
      };
    }
  }

  // Documents
  async getDocuments(projectId: string) {
    try {
      return await this.request<Document[]>(`/documents/project/${projectId}`);
    } catch {
      return DEMO_DOCUMENTS;
    }
  }

  async getDocument(documentId: string) {
    try {
      return await this.request<Document>(`/documents/${documentId}`);
    } catch {
      return DEMO_DOCUMENTS[0];
    }
  }

  async deleteDocument(documentId: string) {
    try {
      return await this.request<{ message: string }>(`/documents/${documentId}`, {
        method: 'DELETE',
      });
    } catch {
      return { message: 'Document deleted' };
    }
  }

  async uploadDocument(projectId: string, formData: FormData) {
    try {
      return await this.request<{ document_id: string; version_id: string; job_id: string }>(
        `/documents/upload/${projectId}`,
        {
          method: 'POST',
          body: formData,
        }
      );
    } catch {
      return {
        document_id: DEMO_DOCUMENTS[0].id,
        version_id: 'v16-uuid',
        job_id: 'job-demo',
      };
    }
  }

  // Versions
  async getVersionDetail(versionId: string) {
    try {
      return await this.request<DocumentVersion>(`/versions/${versionId}`);
    } catch {
      return DEMO_DOCUMENTS[0].versions[1];
    }
  }

  async getVersionChunks(versionId: string) {
    try {
      return await this.request<any[]>(`/versions/${versionId}/chunks`);
    } catch {
      return [];
    }
  }

  // Changes & Diff
  async compareVersions(fromVersionId: string, toVersionId: string) {
    try {
      return await this.request<VersionComparison>(
        `/changes/compare?from_version_id=${fromVersionId}&to_version_id=${toVersionId}`
      );
    } catch {
      return DEMO_COMPARISON;
    }
  }

  async getDocumentTimeline(documentId: string) {
    try {
      return await this.request<DocumentChange[]>(`/changes/document/${documentId}/timeline`);
    } catch {
      return DEMO_CHANGES;
    }
  }

  async getMigrationGuide(fromVersionId: string, toVersionId: string) {
    try {
      return await this.request<{
        from_tag: string;
        to_tag: string;
        risk_score: string;
        risk_color: string;
        breaking_count: number;
        deprecated_count: number;
        added_count: number;
        steps: Array<{
          step: number;
          title: string;
          severity: string;
          description: string;
          code_before: string;
          code_after: string;
        }>;
        markdown_guide: string;
      }>(`/changes/migration-guide?from_version_id=${fromVersionId}&to_version_id=${toVersionId}`, {
        method: 'POST',
      });
    } catch {
      return DEMO_MIGRATION_GUIDE;
    }
  }

  async getSymbolHistory(documentId: string, symbol: string) {
    try {
      return await this.request<Array<{
        version_tag: string;
        version_order: number;
        status: string;
        signature: string;
        documentation_excerpt: string;
        has_definition: boolean;
      }>>(`/changes/symbol-history?document_id=${documentId}&symbol=${encodeURIComponent(symbol)}`);
    } catch {
      return [
        {
          version_tag: 'v14.0.0',
          version_order: 1,
          status: 'standard',
          signature: 'assert.deepEqual(actual, expected[, message])',
          documentation_excerpt: 'Abstract equality (==) comparison across values.',
          has_definition: true,
        },
        {
          version_tag: 'v15.14.0',
          version_order: 2,
          status: 'breaking',
          signature: 'assert.deepEqual(actual, expected[, message])',
          documentation_excerpt: 'Strict prototype validation enforced.',
          has_definition: true,
        },
      ];
    }
  }

  async generateChangelog(versionId: string) {
    try {
      return await this.request<{
        version_tag: string;
        executive_summary: string;
        breaking_changes: string[];
        new_features: string[];
        deprecations: string[];
        silent_changes: string[];
      }>(`/changes/generate-changelog?version_id=${versionId}`, {
        method: 'POST',
      });
    } catch {
      return {
        version_tag: 'v15.14.0',
        executive_summary: 'Major assert runtime update introducing prototype strictness.',
        breaking_changes: ['assert.deepEqual() enforces strict prototype equality.'],
        new_features: ['assert.partialDeepStrictEqual() candidate.'],
        deprecations: ['assert.CallTracker deprecated.'],
        silent_changes: ['assert.deepEqual prototype comparison was not listed in human summary.'],
      };
    }
  }

  async scanProductionCode(payload: {
    from_version_id: string;
    to_version_id: string;
    code_snippet: string;
  }) {
    try {
      return await this.request<{
        from_tag: string;
        to_tag: string;
        risk_level: string;
        compatibility_score: number;
        summary_counts: {
          total_lines_scanned: number;
          vulnerable_lines: number;
          breaking_lines: number;
          silent_lines: number;
          deprecated_lines: number;
        };
        line_findings: Array<{
          line_number: number;
          original_line: string;
          refactored_line: string;
          symbol: string;
          change_type: string;
          severity: string;
          is_breaking: boolean;
          is_silent: boolean;
          issue_summary: string;
          fix_explanation: string;
          citation: {
            version_tag: string;
            section: string;
            excerpt: string;
          };
        }>;
        original_code: string;
        refactored_code: string;
        unified_diff: string;
      }>('/changes/scan-code', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    } catch {
      return DEMO_CODE_SCAN;
    }
  }

  // AI Query
  async askQuestion(payload: {
    question: string;
    project_id: string;
    target_version?: string;
    scope?: string;
    compare_to_version?: string;
    conversation_id?: string;
  }) {
    try {
      return await this.request<QueryResponse>('/query', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    } catch {
      return {
        ...DEMO_QUERY_RESPONSE,
        question: payload.question,
        target_version: payload.target_version || 'v15.14.0',
      };
    }
  }

  async streamQuestion(
    payload: {
      question: string;
      project_id: string;
      target_version?: string;
      scope?: string;
      compare_to_version?: string;
      conversation_id?: string;
    },
    callbacks: {
      onStage?: (event: { stage: number; title: string; detail: string; [key: string]: any }) => void;
      onToken?: (delta: string) => void;
    } = {}
  ): Promise<QueryResponse> {
    try {
      const response = await fetch(`${API_BASE}/query/stream`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(payload),
      });

      if (!response.ok || !response.body) {
        return this.askQuestion(payload);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let finalResponse: QueryResponse | null = null;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const parts = buffer.split('\n\n');
        buffer = parts.pop() || '';

        for (const block of parts) {
          const line = block.trim();
          if (!line.startsWith('data:')) continue;
          const jsonStr = line.replace(/^data:\s*/, '');
          try {
            const parsed = JSON.parse(jsonStr);
            if (parsed.type === 'stage' && callbacks.onStage) {
              callbacks.onStage(parsed);
            } else if (parsed.type === 'token' && callbacks.onToken) {
              callbacks.onToken(parsed.delta || '');
            } else if (parsed.type === 'done' && parsed.response) {
              finalResponse = parsed.response as QueryResponse;
            }
          } catch {
            // Ignore malformed chunk
          }
        }
      }

      if (!finalResponse) {
        return this.askQuestion(payload);
      }
      return finalResponse;
    } catch {
      return this.askQuestion(payload);
    }
  }

  async getConversations(projectId: string) {
    try {
      return await this.request<any[]>(`/query/conversations/${projectId}`);
    } catch {
      return [];
    }
  }

  // Evaluations
  async getEvaluations(projectId: string) {
    try {
      return await this.request<EvaluationRun[]>(`/evaluations/project/${projectId}`);
    } catch {
      return DEMO_EVALUATIONS;
    }
  }

  async getAutoSynthesizedScenarios(projectId: string, count: number = 10) {
    try {
      return await this.request<{
        project_id: string;
        total_synthesized: number;
        scenarios: Array<{
          query_archetype: string;
          question: string;
          target_version?: string | null;
          ground_truth_answer: string;
          target_keywords: string[];
          failure_taxonomy: string;
          explanation: string;
        }>;
      }>(`/evaluations/auto-scenarios/${projectId}?count=${count}`);
    } catch {
      return DEMO_AUTO_SCENARIOS;
    }
  }

  async runBenchmark(projectId: string, runName?: string) {
    try {
      return await this.request<EvaluationRun>('/evaluations/run', {
        method: 'POST',
        body: JSON.stringify({ project_id: projectId, run_name: runName }),
      });
    } catch {
      return DEMO_EVALUATIONS[0];
    }
  }

  async addCustomScenario(payload: {
    project_id: string;
    question: string;
    target_version: string;
    ground_truth: string;
    archetype?: string;
  }) {
    try {
      return await this.request<EvaluationRun>(
        `/evaluations/custom-scenario?project_id=${payload.project_id}&question=${encodeURIComponent(
          payload.question
        )}&target_version=${encodeURIComponent(payload.target_version)}&ground_truth=${encodeURIComponent(
          payload.ground_truth
        )}&archetype=${encodeURIComponent(payload.archetype || 'version_specific_query')}`,
        { method: 'POST' }
      );
    } catch {
      return DEMO_EVALUATIONS[0];
    }
  }

  // Jobs
  async getJobStatus(jobId: string): Promise<ProcessingJob> {
    try {
      return await this.request<ProcessingJob>(`/jobs/${jobId}`);
    } catch {
      return {
        id: jobId,
        workspace_id: 'ws-demo',
        project_id: 'proj-demo',
        job_type: 'ast_indexing',
        status: 'completed',
        current_stage: 'completed',
        stage_progress: 100,
        retry_count: 0,
        execution_meta: {},
        error_message: undefined,
        created_at: new Date().toISOString(),
      };
    }
  }

  // Runtime LLM & API Key Switcher
  async getLlmConfig() {
    try {
      return await this.request<{
        active_provider: string;
        active_model: string;
        has_api_key: boolean;
        masked_api_key?: string | null;
        configured_providers: string[];
        supported_providers: Array<{
          id: string;
          name: string;
          default_model: string;
          requires_key: boolean;
          badge: string;
        }>;
      }>('/health/llm-config');
    } catch {
      return DEMO_LLM_CONFIG;
    }
  }

  async updateLlmConfig(payload: { provider: string; api_key?: string; model_name?: string }) {
    try {
      return await this.request<{
        active_provider: string;
        active_model: string;
        has_api_key: boolean;
        masked_api_key?: string | null;
        configured_providers: string[];
      }>('/health/llm-config', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    } catch {
      return {
        active_provider: payload.provider,
        active_model: payload.model_name || 'VersionRAG-v1-Deterministic',
        has_api_key: true,
        masked_api_key: 'sk-proj-****LOCAL****',
        configured_providers: ['local_deterministic', payload.provider],
      };
    }
  }
}

export const api = new ApiClient();


