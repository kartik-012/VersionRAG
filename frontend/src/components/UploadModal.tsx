import React, { useState } from 'react';
import { UploadCloud, File, CheckCircle2, AlertCircle, Loader2, X } from 'lucide-react';
import { api } from '../lib/api';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  onUploadComplete: () => void;
}

const STAGES = [
  'Validating File',
  'Parsing Content',
  'Extracting Metadata',
  'Detecting Version',
  'Clustering Family',
  'Chunking Document',
  'Generating Embeddings',
  'Detecting Changes',
  'Indexing Knowledge Base',
  'Ready',
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
  const [currentStageIdx, setCurrentStageIdx] = useState(0);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setError(null);
    setCurrentStageIdx(0);

    const formData = new FormData();
    formData.append('file', file);
    if (versionTag.trim()) {
      formData.append('version_tag', versionTag.trim());
    }

    try {
      // Simulate stage progression while processing job runs
      const stageInterval = setInterval(() => {
        setCurrentStageIdx((prev) => (prev < STAGES.length - 1 ? prev + 1 : prev));
      }, 500);

      const res = await api.uploadDocument(projectId, formData);
      clearInterval(stageInterval);
      setCurrentStageIdx(STAGES.length - 1);

      setTimeout(() => {
        setIsUploading(false);
        onUploadComplete();
        onClose();
      }, 800);
    } catch (err: any) {
      setError(err.message || 'Upload failed');
      setIsUploading(false);
    }
  };

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
          /* Live 10-Stage Pipeline Progress */
          <div className="py-6 space-y-5">
            <div className="text-center">
              <Loader2 className="w-8 h-8 text-primary animate-spin mx-auto mb-2" />
              <p className="text-sm font-semibold text-white">{STAGES[currentStageIdx]}</p>
              <p className="text-xs text-gray-400 mt-1">
                Stage {currentStageIdx + 1} of {STAGES.length}
              </p>
            </div>

            {/* Stage Checklist */}
            <div className="bg-surface-subtle border border-surface-border rounded-lg p-3.5 space-y-2 max-h-48 overflow-y-auto">
              {STAGES.map((st, i) => {
                const isPassed = i < currentStageIdx;
                const isCurrent = i === currentStageIdx;
                return (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    {isPassed ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    ) : isCurrent ? (
                      <Loader2 className="w-3.5 h-3.5 text-primary animate-spin" />
                    ) : (
                      <div className="w-3.5 h-3.5 rounded-full border border-gray-600" />
                    )}
                    <span
                      className={
                        isPassed ? 'text-gray-400 line-through' : isCurrent ? 'text-white font-semibold' : 'text-gray-600'
                      }
                    >
                      {st}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
