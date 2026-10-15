import {
  User, Workspace, Project, Document, DocumentVersion,
  DocumentChange, VersionComparison, QueryResponse, ProcessingJob,
  EvaluationRun
} from '../types';

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
        'Cannot connect to backend server. Please verify the FastAPI backend is running on port 8001.'
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
  }

  async signup(email: string, full_name: string, password: string) {
    return this.request<{ message: string; requires_verification: boolean; email: string }>(
      '/auth/signup',
      {
        method: 'POST',
        body: JSON.stringify({ email, full_name, password }),
      }
    );
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
    return this.request<User>('/auth/me');
  }

  logout() {
    localStorage.removeItem('versionrag_access_token');
    localStorage.removeItem('versionrag_refresh_token');
  }

  // Workspaces
  async getWorkspaces() {
    return this.request<Workspace[]>('/workspaces');
  }

  async createWorkspace(name: string, description?: string) {
    return this.request<Workspace>('/workspaces', {
      method: 'POST',
      body: JSON.stringify({ name, description }),
    });
  }

  async getWorkspaceMembers(workspaceId: string) {
    return this.request<any[]>(`/workspaces/${workspaceId}/members`);
  }

  // Projects
  async getProjects(workspaceId: string) {
    return this.request<Project[]>(`/projects/workspace/${workspaceId}`);
  }

  async createProject(workspaceId: string, name: string, description?: string) {
    return this.request<Project>(`/projects/workspace/${workspaceId}`, {
      method: 'POST',
      body: JSON.stringify({ name, description }),
    });
  }

  // Documents
  async getDocuments(projectId: string) {
    return this.request<Document[]>(`/documents/project/${projectId}`);
  }

  async getDocument(documentId: string) {
    return this.request<Document>(`/documents/${documentId}`);
  }

  async deleteDocument(documentId: string) {
    return this.request<{ message: string }>(`/documents/${documentId}`, {
      method: 'DELETE',
    });
  }

  async uploadDocument(projectId: string, formData: FormData) {
    return this.request<{ document_id: string; version_id: string; job_id: string }>(
      `/documents/upload/${projectId}`,
      {
        method: 'POST',
        body: formData,
      }
    );
  }

  // Versions
  async getVersionDetail(versionId: string) {
    return this.request<DocumentVersion>(`/versions/${versionId}`);
  }

  async getVersionChunks(versionId: string) {
    return this.request<any[]>(`/versions/${versionId}/chunks`);
  }

  // Changes & Diff
  async compareVersions(fromVersionId: string, toVersionId: string) {
    return this.request<VersionComparison>(
      `/changes/compare?from_version_id=${fromVersionId}&to_version_id=${toVersionId}`
    );
  }

  async getDocumentTimeline(documentId: string) {
    return this.request<DocumentChange[]>(`/changes/document/${documentId}/timeline`);
  }

  async getMigrationGuide(fromVersionId: string, toVersionId: string) {
    return this.request<{
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
  }

  async getSymbolHistory(documentId: string, symbol: string) {
    return this.request<Array<{
      version_tag: string;
      version_order: number;
      status: string;
      signature: string;
      documentation_excerpt: string;
      has_definition: boolean;
    }>>(`/changes/symbol-history?document_id=${documentId}&symbol=${encodeURIComponent(symbol)}`);
  }

  async generateChangelog(versionId: string) {
    return this.request<{
      version_tag: string;
      executive_summary: string;
      breaking_changes: string[];
      new_features: string[];
      deprecations: string[];
      silent_changes: string[];
    }>(`/changes/generate-changelog?version_id=${versionId}`, {
      method: 'POST',
    });
  }

  async scanProductionCode(payload: {
    from_version_id: string;
    to_version_id: string;
    code_snippet: string;
  }) {
    return this.request<{
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
    return this.request<QueryResponse>('/query', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
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
    let response: Response;
    try {
      response = await fetch(`${API_BASE}/query/stream`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(payload),
      });
    } catch {
      return this.askQuestion(payload);
    }

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
  }

  async getConversations(projectId: string) {
    return this.request<any[]>(`/query/conversations/${projectId}`);
  }

  // Evaluations
  async getEvaluations(projectId: string) {
    return this.request<EvaluationRun[]>(`/evaluations/project/${projectId}`);
  }

  async getAutoSynthesizedScenarios(projectId: string, count: number = 10) {
    return this.request<{
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
  }

  async runBenchmark(projectId: string, runName?: string) {
    return this.request<EvaluationRun>('/evaluations/run', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, run_name: runName }),
    });
  }

  async addCustomScenario(payload: {
    project_id: string;
    question: string;
    target_version: string;
    ground_truth: string;
    archetype?: string;
  }) {
    return this.request<EvaluationRun>(
      `/evaluations/custom-scenario?project_id=${payload.project_id}&question=${encodeURIComponent(
        payload.question
      )}&target_version=${encodeURIComponent(payload.target_version)}&ground_truth=${encodeURIComponent(
        payload.ground_truth
      )}&archetype=${encodeURIComponent(payload.archetype || 'version_specific_query')}`,
      { method: 'POST' }
    );
  }

  // Jobs
  async getJobStatus(jobId: string) {
    return this.request<ProcessingJob>(`/jobs/${jobId}`);
  }

  // Runtime LLM & API Key Switcher
  async getLlmConfig() {
    return this.request<{
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
  }

  async updateLlmConfig(payload: { provider: string; api_key?: string; model_name?: string }) {
    return this.request<{
      active_provider: string;
      active_model: string;
      has_api_key: boolean;
      masked_api_key?: string | null;
      configured_providers: string[];
    }>('/health/llm-config', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }
}

export const api = new ApiClient();


