import React, { useState, useEffect } from 'react';
import {
  GitPullRequest, ArrowRight, ShieldAlert,
  Download, Sparkles, CheckCircle2, Code2, AlertTriangle, Copy, Check
} from 'lucide-react';
import { Document, DocumentVersion } from '../types';
import { VersionBadge } from '../components/VersionBadge';
import { api } from '../lib/api';

interface MigrationGuideViewProps {
  documents: Document[];
}

export const MigrationGuideView: React.FC<MigrationGuideViewProps> = ({ documents }) => {
  const [selectedDocId, setSelectedDocId] = useState<string>(documents[0]?.id || '');
  const [fromVersionId, setFromVersionId] = useState<string>('');
  const [toVersionId, setToVersionId] = useState<string>('');
  const [guideData, setGuideData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const selectedDoc = documents.find((d) => d.id === selectedDocId);

  useEffect(() => {
    if (selectedDoc && selectedDoc.versions.length >= 2) {
      setFromVersionId(selectedDoc.versions[0].id);
      setToVersionId(selectedDoc.versions[selectedDoc.versions.length - 1].id);
    }
  }, [selectedDocId]);

  const handleGenerate = async () => {
    if (!fromVersionId || !toVersionId) return;
    setLoading(true);
    try {
      const res = await api.getMigrationGuide(fromVersionId, toVersionId);
      setGuideData(res);
    } catch (err: any) {
      alert(err.message || 'Failed to generate migration guide');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyMarkdown = () => {
    if (guideData?.markdown_guide) {
      navigator.clipboard.writeText(guideData.markdown_guide);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadMarkdown = () => {
    if (guideData?.markdown_guide) {
      const blob = new Blob([guideData.markdown_guide], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Migration_Guide_${guideData.from_tag}_to_${guideData.to_tag}.md`;
      a.click();
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-surface border border-surface-border rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              <GitPullRequest className="w-5 h-5 text-indigo-400" />
              Automated Migration Guide & Refactoring Synthesizer
            </h1>
            <p className="text-xs text-gray-400 mt-0.5">
              Generates step-by-step upgrade instructions and before/after code transformations.
            </p>
          </div>

          <button
            onClick={handleGenerate}
            disabled={loading || !fromVersionId || !toVersionId}
            className="px-5 py-2 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-semibold shadow-md shadow-primary/30 flex items-center gap-2 transition disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4" />
            <span>{loading ? 'Synthesizing Roadmap...' : 'Generate Migration Guide'}</span>
          </button>
        </div>

        {/* Version Selectors */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-surface-border">
          <div>
            <label className="block text-[11px] font-medium text-gray-400 mb-1">Document Family</label>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="w-full bg-surface-subtle border border-surface-border text-xs rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary"
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.title}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-gray-400 mb-1">Current Base Version (From)</label>
            <select
              value={fromVersionId}
              onChange={(e) => setFromVersionId(e.target.value)}
              className="w-full bg-surface-subtle border border-surface-border text-xs rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary font-mono"
            >
              {selectedDoc?.versions.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.version_tag}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-gray-400 mb-1">Target Upgrade Version (To)</label>
            <select
              value={toVersionId}
              onChange={(e) => setToVersionId(e.target.value)}
              className="w-full bg-surface-subtle border border-surface-border text-xs rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary font-mono"
            >
              {selectedDoc?.versions.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.version_tag}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Guide Content */}
      {guideData ? (
        <div className="space-y-6">
          {/* Risk Level Banner */}
          <div className="p-5 rounded-2xl bg-surface border border-surface-border shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm ${
                  guideData.risk_score === 'CRITICAL'
                    ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                    : guideData.risk_score === 'HIGH'
                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                }`}
              >
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-white">Migration Risk Assessment:</span>
                  <span
                    className={`text-xs font-mono font-bold uppercase px-2 py-0.5 rounded ${
                      guideData.risk_score === 'CRITICAL'
                        ? 'bg-rose-500/20 text-rose-400'
                        : guideData.risk_score === 'HIGH'
                        ? 'bg-amber-500/20 text-amber-400'
                        : 'bg-emerald-500/20 text-emerald-400'
                    }`}
                  >
                    {guideData.risk_score} RISK
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-0.5">
                  Trajectory: <span className="font-mono text-gray-200">{guideData.from_tag}</span> →{' '}
                  <span className="font-mono text-gray-200">{guideData.to_tag}</span> (
                  {guideData.breaking_count} breaking changes, {guideData.deprecated_count} deprecations)
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleCopyMarkdown}
                className="px-3 py-1.5 rounded-lg bg-surface-subtle hover:bg-surface-hover border border-surface-border text-gray-200 text-xs font-medium flex items-center gap-1.5 transition"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied' : 'Copy Guide'}</span>
              </button>
              <button
                onClick={handleDownloadMarkdown}
                className="px-3 py-1.5 rounded-lg bg-surface-subtle hover:bg-surface-hover border border-surface-border text-gray-200 text-xs font-medium flex items-center gap-1.5 transition"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download .MD</span>
              </button>
            </div>
          </div>

          {/* Refactoring Steps */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Code2 className="w-4 h-4 text-primary" />
              Automated Code Transformation Steps ({guideData.steps.length})
            </h3>

            {guideData.steps.map((st: any) => (
              <div
                key={st.step}
                className="bg-surface border border-surface-border rounded-2xl p-5 shadow-sm space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="w-6 h-6 rounded-full bg-primary/20 text-primary-light flex items-center justify-center font-mono font-bold text-xs">
                      {st.step}
                    </span>
                    <h4 className="text-sm font-semibold text-white">{st.title}</h4>
                  </div>
                  <span
                    className={`text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded ${
                      st.severity === 'CRITICAL'
                        ? 'bg-rose-500/20 text-rose-400'
                        : st.severity === 'HIGH'
                        ? 'bg-amber-500/20 text-amber-400'
                        : 'bg-emerald-500/20 text-emerald-400'
                    }`}
                  >
                    {st.severity}
                  </span>
                </div>

                <p className="text-xs text-gray-300">{st.description}</p>

                {/* Code Before & After Comparison */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 text-xs font-mono">
                  <div className="p-3 rounded-xl bg-background border border-rose-500/20 text-rose-300">
                    <div className="text-[10px] uppercase font-bold text-rose-400 mb-1.5 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                      Legacy Code ({guideData.from_tag})
                    </div>
                    <pre className="text-[11px] whitespace-pre-wrap leading-relaxed">{st.code_before}</pre>
                  </div>

                  <div className="p-3 rounded-xl bg-background border border-emerald-500/20 text-emerald-300">
                    <div className="text-[10px] uppercase font-bold text-emerald-400 mb-1.5 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      Refactored Code ({guideData.to_tag})
                    </div>
                    <pre className="text-[11px] whitespace-pre-wrap leading-relaxed">{st.code_after}</pre>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-16 bg-surface border border-surface-border rounded-2xl p-8">
          <GitPullRequest className="w-10 h-10 text-indigo-400 mx-auto mb-3 opacity-60" />
          <h3 className="text-sm font-semibold text-white">No migration guide synthesized yet</h3>
          <p className="text-xs text-gray-400 mt-1 max-w-md mx-auto">
            Select your base and target versions above, then click 'Generate Migration Guide' to produce an automated refactoring roadmap.
          </p>
        </div>
      )}
    </div>
  );
};
