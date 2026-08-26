import React, { useState, useEffect } from 'react';
import {
  GitCompare, ArrowRight, ShieldAlert,
  EyeOff, Plus, Minus, Edit3, Filter, Code2, Columns
} from 'lucide-react';
import { Document, VersionComparison, DocumentChange } from '../types';
import { VersionBadge } from '../components/VersionBadge';
import { ChangeBadge } from '../components/ChangeBadge';
import { api } from '../lib/api';

interface DiffViewProps {
  documents: Document[];
  onOpenEvidence?: (change: DocumentChange) => void;
}

export const DiffView: React.FC<DiffViewProps> = ({ documents }) => {
  const allVersions = documents.flatMap((d) => d.versions);
  const [selectedDocId, setSelectedDocId] = useState<string>(documents[0]?.id || '');
  const [fromVersionId, setFromVersionId] = useState<string>('');
  const [toVersionId, setToVersionId] = useState<string>('');
  const [mode, setMode] = useState<'unified' | 'changes'>('changes');
  const [comparison, setComparison] = useState<VersionComparison | null>(null);
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState<string>('all');

  const selectedDoc = documents.find((d) => d.id === selectedDocId);

  useEffect(() => {
    if (selectedDoc && selectedDoc.versions.length >= 2) {
      setFromVersionId(selectedDoc.versions[0].id);
      setToVersionId(selectedDoc.versions[1].id);
    }
  }, [selectedDocId]);

  useEffect(() => {
    const fetchDiff = async () => {
      if (!fromVersionId || !toVersionId) return;
      setLoading(true);
      try {
        const res = await api.compareVersions(fromVersionId, toVersionId);
        setComparison(res);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchDiff();
  }, [fromVersionId, toVersionId]);

  const filteredChanges = (comparison?.changes || []).filter((c) => {
    if (filterType === 'all') return true;
    if (filterType === 'breaking') return c.is_breaking;
    if (filterType === 'silent') return c.is_silent;
    return c.change_type === filterType;
  });

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header Controls */}
      <div className="bg-surface border border-surface-border rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              <GitCompare className="w-5 h-5 text-purple-400" />
              Version Comparison & Structural Diff Studio
            </h1>
            <p className="text-xs text-gray-400 mt-0.5">
              Inspect explicit changelogs and implicit structural diffs between releases.
            </p>
          </div>

          <div className="flex items-center gap-2 bg-surface-subtle p-1 rounded-lg border border-surface-border">
            <button
              onClick={() => setMode('changes')}
              className={`px-3 py-1.5 rounded text-xs font-medium transition flex items-center gap-1.5 ${
                mode === 'changes' ? 'bg-primary text-white font-semibold' : 'text-gray-400 hover:text-white'
              }`}
            >
              <Columns className="w-3.5 h-3.5" />
              Categorized Changes
            </button>
            <button
              onClick={() => setMode('unified')}
              className={`px-3 py-1.5 rounded text-xs font-medium transition flex items-center gap-1.5 ${
                mode === 'unified' ? 'bg-primary text-white font-semibold' : 'text-gray-400 hover:text-white'
              }`}
            >
              <Code2 className="w-3.5 h-3.5" />
              Unified Code Diff
            </button>
          </div>
        </div>

        {/* Version Pickers */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-surface-border">
          <div>
            <label className="block text-[11px] font-medium text-gray-400 mb-1">Document</label>
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
            <label className="block text-[11px] font-medium text-gray-400 mb-1">Base Version (From)</label>
            <select
              value={fromVersionId}
              onChange={(e) => setFromVersionId(e.target.value)}
              className="w-full bg-surface-subtle border border-surface-border text-xs rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary"
            >
              {selectedDoc?.versions.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.version_tag} ({v.source_filename || 'source.md'})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-gray-400 mb-1">Target Version (To)</label>
            <select
              value={toVersionId}
              onChange={(e) => setToVersionId(e.target.value)}
              className="w-full bg-surface-subtle border border-surface-border text-xs rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary"
            >
              {selectedDoc?.versions.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.version_tag} ({v.source_filename || 'source.md'})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Summary Stat Pills */}
      {comparison && (
        <div className="flex flex-wrap gap-2 text-xs">
          <button
            onClick={() => setFilterType('all')}
            className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition ${
              filterType === 'all' ? 'bg-primary text-white border-primary' : 'bg-surface border-surface-border text-gray-400 hover:text-white'
            }`}
          >
            All Changes ({comparison.summary.total || 0})
          </button>
          <button
            onClick={() => setFilterType('breaking')}
            className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition flex items-center gap-1.5 ${
              filterType === 'breaking'
                ? 'bg-fuchsia-500/20 text-fuchsia-300 border-fuchsia-500'
                : 'bg-surface border-surface-border text-fuchsia-400 hover:text-white'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            Breaking ({comparison.summary.breaking || 0})
          </button>
          <button
            onClick={() => setFilterType('silent')}
            className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition flex items-center gap-1.5 ${
              filterType === 'silent'
                ? 'bg-purple-500/20 text-purple-300 border-purple-500'
                : 'bg-surface border-surface-border text-purple-400 hover:text-white'
            }`}
          >
            <EyeOff className="w-3.5 h-3.5" />
            Silent / Undocumented ({comparison.summary.silent || 0})
          </button>
          <button
            onClick={() => setFilterType('deprecated')}
            className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition ${
              filterType === 'deprecated'
                ? 'bg-amber-500/20 text-amber-300 border-amber-500'
                : 'bg-surface border-surface-border text-amber-400 hover:text-white'
            }`}
          >
            Deprecated ({comparison.summary.deprecated || 0})
          </button>
          <button
            onClick={() => setFilterType('added')}
            className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition ${
              filterType === 'added'
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500'
                : 'bg-surface border-surface-border text-emerald-400 hover:text-white'
            }`}
          >
            Added ({comparison.summary.added || 0})
          </button>
        </div>
      )}

      {/* Main Diff Content */}
      {mode === 'changes' ? (
        <div className="space-y-3">
          {filteredChanges.map((ch) => (
            <div
              key={ch.id}
              className={`p-4 bg-surface border rounded-xl shadow-sm space-y-3 transition ${
                ch.is_breaking
                  ? 'border-fuchsia-500/40 bg-fuchsia-950/10'
                  : ch.is_silent
                  ? 'border-purple-500/40 bg-purple-950/10'
                  : 'border-surface-border'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className="font-mono text-sm font-bold text-white">{ch.location}</span>
                  <ChangeBadge type={ch.change_type} isBreaking={ch.is_breaking} isSilent={ch.is_silent} />
                </div>
                <span className="text-xs font-mono text-gray-400">
                  {ch.from_version_tag} → {ch.to_version_tag}
                </span>
              </div>

              <p className="text-xs text-gray-300 font-medium">{ch.summary}</p>

              {(ch.old_content || ch.new_content) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 text-xs font-mono">
                  {ch.old_content && (
                    <div className="p-3 rounded-lg bg-background border border-rose-500/20 text-rose-300">
                      <div className="text-[10px] uppercase font-bold text-rose-400 mb-1">
                        Previous ({ch.from_version_tag})
                      </div>
                      <div className="text-[11px] whitespace-pre-wrap">{ch.old_content}</div>
                    </div>
                  )}
                  {ch.new_content && (
                    <div className="p-3 rounded-lg bg-background border border-emerald-500/20 text-emerald-300">
                      <div className="text-[10px] uppercase font-bold text-emerald-400 mb-1">
                        Updated ({ch.to_version_tag})
                      </div>
                      <div className="text-[11px] whitespace-pre-wrap">{ch.new_content}</div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {filteredChanges.length === 0 && (
            <div className="p-12 text-center text-xs text-gray-500 bg-surface border border-surface-border rounded-xl">
              No changes found matching the selected filter.
            </div>
          )}
        </div>
      ) : (
        /* Unified Code Diff View */
        <div className="bg-surface border border-surface-border rounded-xl p-5 shadow-sm">
          <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-3 font-mono">
            Unified Line-by-Line Diff
          </h3>
          <div className="bg-background border border-surface-border rounded-lg p-4 font-mono text-xs overflow-x-auto leading-relaxed">
            {comparison?.unified_diff ? (
              comparison.unified_diff.split('\n').map((line, i) => {
                const isAdd = line.startsWith('+') && !line.startsWith('+++');
                const isDel = line.startsWith('-') && !line.startsWith('---');
                const isHunk = line.startsWith('@@');

                return (
                  <div
                    key={i}
                    className={`py-0.5 px-2 rounded-sm ${
                      isAdd
                        ? 'diff-add'
                        : isDel
                        ? 'diff-del'
                        : isHunk
                        ? 'text-cyan-400 bg-cyan-950/20 font-bold'
                        : 'text-gray-300'
                    }`}
                  >
                    {line}
                  </div>
                );
              })
            ) : (
              <p className="text-gray-500">No textual difference found.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
