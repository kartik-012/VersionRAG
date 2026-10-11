import React, { useState } from 'react';
import { UploadCloud, CheckCircle2, AlertCircle, Loader2, X, Cpu } from 'lucide-react';
import { api } from '../lib/api';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  onUploadComplete: () => void;
}

const PIPELINE_MILESTONES = [
  { progress: 0.20, stage: 'parsing', label: 'Stage 1 (20%): Validating & Parsing Document' },
  { progress: 0.45, stage: 'chunking', label: 'Stage 2 (45%): Version Detection & Structure Chunking' },
  { progress: 0.70, stage: 'generating_embeddings', label: 'Stage 3 (70%): Semantic Embeddings & Hybrid Partition Indexing' },
  { progress: 0.90, stage: 'detecting_changes', label: 'Stage 4 (90%): AST Signature & Implicit Diff Detection' },
  { progress: 1.00, stage: 'ready', label: 'Stage 5 (100%): Knowledge Base Partition Ready' },
];

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  projectId,
  onUploadComplete,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [versionTag, setVersionTag] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [stageProgress, setStageProgress] = useState<number>(0);
  const [jobTelemetry, setJobTelemetry] = useState<Record<string, any>>({});
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const pollJobUntilComplete = async (jobId: string) => {
    const maxAttempts = 60;
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const job = await api.getJobStatus(jobId);
      setStageProgress(job.stage_progress || 0.2);
      setJobTelemetry(job.execution_meta || {});

      if (job.status === 'completed' || job.current_stage === 'ready') {
        setStageProgress(1.0);
        return job;
      }
      if (job.status === 'failed' || job.current_stage === 'failed') {
        throw new Error(job.error_message || 'Background ingestion job failed');
      }
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
    throw new Error('Ingestion job timed out waiting for worker completion');
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setError(null);
    setStageProgress(0.1);
    setJobTelemetry({});

    const formData = new FormData();
    formData.append('file', file);
    if (versionTag.trim()) {
      formData.append('version_tag', versionTag.trim());
    }

    try {
      const res = await api.uploadDocument(projectId, formData);
      if (res.job_id) {
        await pollJobUntilComplete(res.job_id);
      } else {
        setStageProgress(1.0);
      }

      setTimeout(() => {
        setIsUploading(false);
        setFile(null);
        setVersionTag('');
        onUploadComplete();
        onClose();
      }, 650);
    } catch (err: any) {
      setError(err.message || 'Upload failed');
      setIsUploading(false);
    }
  };

  const activeMilestoneIdx = PIPELINE_MILESTONES.findIndex((m) => stageProgress <= m.progress);
  const resolvedIdx = activeMilestoneIdx === -1 ? PIPELINE_MILESTONES.length - 1 : activeMilestoneIdx;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-surface border border-surface-border w-full max-w-lg rounded-xl shadow-2xl p-6 relative">
        <button
          onClick={onClose}
          disabled={isUploading}
          className="absolute top-4 right-4 text-gray-400 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>

        <h3 className="text-base font-semibold text-white mb-1">Upload Document Version</h3>
        <p className="text-xs text-gray-400 mb-5">
          Supported formats: PDF, Markdown, TXT, HTML, DOCX (up to 50MB).
        </p>

        {/* Drop Zone */}
        {!isUploading ? (
          <div className="space-y-4">
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleFileDrop}
              className="border-2 border-dashed border-surface-border hover:border-primary/50 bg-surface-subtle/50 rounded-xl p-8 text-center cursor-pointer transition"
              onClick={() => document.getElementById('file-upload-input')?.click()}
            >
              <input
                id="file-upload-input"
                type="file"
                className="hidden"
                accept=".pdf,.md,.markdown,.txt,.html,.docx"
                onChange={(e) => e.target.files && setFile(e.target.files[0])}
              />
              <UploadCloud className="w-10 h-10 text-primary-light mx-auto mb-3" />
              <p className="text-sm font-medium text-gray-200">
                {file ? file.name : 'Click to select or drag & drop document file'}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {file ? `${(file.size / 1024).toFixed(1)} KB` : 'PDF, Markdown, TXT, HTML, DOCX'}
              </p>
            </div>

            {/* Version Tag Override (Optional) */}
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">
                Version Tag (Optional - auto-detected if left empty)
              </label>
              <input
                type="text"
                placeholder="e.g. v15.14.0 or 2025.1"
                value={versionTag}
                onChange={(e) => setVersionTag(e.target.value)}
                className="w-full bg-surface-subtle border border-surface-border rounded-lg px-3 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-primary"
              />
            </div>

            {error && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-lg text-xs font-medium text-gray-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleUpload}
                disabled={!file}
                className="px-5 py-2 rounded-lg text-xs font-semibold bg-primary hover:bg-primary-hover text-white disabled:opacity-50 transition shadow-sm shadow-primary/30"
              >
                Start Ingestion Pipeline
              </button>
            </div>
          </div>
        ) : (
          /* Live 5-Stage Telemetry Progress */
          <div className="py-5 space-y-4">
            <div className="text-center">
              <Loader2 className="w-8 h-8 text-primary animate-spin mx-auto mb-2" />
              <p className="text-sm font-semibold text-white">
                {PIPELINE_MILESTONES[resolvedIdx]?.label}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                Real-Time Worker Telemetry: {Math.round(stageProgress * 100)}% Complete
              </p>
            </div>

            {/* Progress Bar */}
            <div className="w-full h-2 bg-surface-subtle rounded-full overflow-hidden border border-surface-border">
              <div
                className="h-full bg-primary transition-all duration-300"
                style={{ width: `${Math.round(stageProgress * 100)}%` }}
              />
            </div>

            {/* 5-Stage Checklist */}
            <div className="bg-surface-subtle border border-surface-border rounded-lg p-3.5 space-y-2.5">
              {PIPELINE_MILESTONES.map((m, i) => {
                const isPassed = stageProgress >= m.progress;
                const isCurrent = i === resolvedIdx && !isPassed;
                return (
                  <div key={m.stage} className="flex items-center gap-2.5 text-xs">
                    {isPassed ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : isCurrent ? (
                      <Loader2 className="w-4 h-4 text-primary animate-spin shrink-0" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border border-gray-600 shrink-0" />
                    )}
                    <span
                      className={
                        isPassed
                          ? 'text-emerald-300 font-medium'
                          : isCurrent
                          ? 'text-white font-semibold'
                          : 'text-gray-500'
                      }
                    >
                      {m.label}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Live Worker Telemetry Badges */}
            {Object.keys(jobTelemetry).length > 0 && (
              <div className="bg-surface-subtle/60 border border-surface-border rounded-lg p-3 text-[11px] text-gray-300 flex flex-wrap gap-2 items-center">
                <span className="flex items-center gap-1 text-primary-light font-semibold">
                  <Cpu className="w-3.5 h-3.5" /> Telemetry:
                </span>
                {jobTelemetry.detected_version && (
                  <span className="px-2 py-0.5 rounded bg-surface border border-surface-border">
                    Version: <b>{jobTelemetry.detected_version}</b>
                  </span>
                )}
                {typeof jobTelemetry.chunks_created === 'number' && (
                  <span className="px-2 py-0.5 rounded bg-surface border border-surface-border">
                    Chunks: <b>{jobTelemetry.chunks_created}</b>
                  </span>
                )}
                {typeof jobTelemetry.changes_detected === 'number' && (
                  <span className="px-2 py-0.5 rounded bg-surface border border-surface-border">
                    Diffs: <b>{jobTelemetry.changes_detected}</b> ({jobTelemetry.silent_changes || 0} silent)
                  </span>
                )}
                {typeof jobTelemetry.duration_ms === 'number' && (
                  <span className="px-2 py-0.5 rounded bg-surface border border-surface-border">
                    Time: <b>{jobTelemetry.duration_ms}ms</b>
                  </span>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

