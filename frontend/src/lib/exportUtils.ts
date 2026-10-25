import { EvaluationRun } from '../types';

/**
 * Downloads an EvaluationRun object as a formatted JSON report.
 */
export function exportEvaluationAsJson(run: EvaluationRun, filename?: string): void {
  const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(run, null, 2));
  const downloadAnchor = document.createElement('a');
  const safeName = (filename || `${run.dataset_name || 'versionrag'}-benchmark-report`).replace(/[^a-zA-Z0-9_-]/g, '_');
  downloadAnchor.setAttribute('href', dataStr);
  downloadAnchor.setAttribute('download', `${safeName}.json`);
  document.body.appendChild(downloadAnchor);
  downloadAnchor.click();
  downloadAnchor.remove();
}

/**
 * Downloads scenario results as a flat CSV matrix for spreadsheet analysis.
 */
export function exportScenariosAsCsv(run: EvaluationRun, filename?: string): void {
  const headers = [
    'Scenario ID',
    'Query Archetype',
    'Question',
    'Target Version',
    'Naive RAG Correct',
    'VersionRAG Correct',
    'Confidence',
    'Execution Time (ms)',
  ];

  const rows = (run.results || []).map((r) => [
    `"${r.id}"`,
    `"${r.query_archetype || ''}"`,
    `"${(r.question || '').replace(/"/g, '""')}"`,
    `"${r.target_version || ''}"`,
    r.naive_rag_correct ?? 0,
    r.versionrag_correct ?? 0,
    `"${r.versionrag_confidence || ''}"`,
    r.execution_time_ms ?? 0,
  ]);

  const csvContent = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  const safeName = (filename || `${run.dataset_name || 'versionrag'}-scenarios`).replace(/[^a-zA-Z0-9_-]/g, '_');
  link.setAttribute('href', url);
  link.setAttribute('download', `${safeName}.csv`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
