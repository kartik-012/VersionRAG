import React, { useState } from 'react';
import { Search, Code2, AlertTriangle, CheckCircle2, XCircle, ArrowRight, ShieldCheck, Sparkles } from 'lucide-react';
import { Document } from '../types';
import { VersionBadge } from '../components/VersionBadge';
import { api } from '../lib/api';

interface SymbolHistoryViewProps {
  documents: Document[];
}

export const SymbolHistoryView: React.FC<SymbolHistoryViewProps> = ({ documents }) => {
  const [selectedDocId, setSelectedDocId] = useState<string>(documents[0]?.id || '');
  const [symbolQuery, setSymbolQuery] = useState('assert.deepEqual');
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const sampleSymbols = [
    'assert.deepEqual',
    'assert.partialDeepStrictEqual',
    'assert.CallTracker',
    'assert.strictEqual',
  ];

  const handleSearch = async (query?: string) => {
    const sym = query || symbolQuery;
    if (!selectedDocId || !sym.trim()) return;

    setLoading(true);
    try {
      const res = await api.getSymbolHistory(selectedDocId, sym.trim());
      setHistory(res);
    } catch (err: any) {
      alert(err.message || 'Symbol history extraction failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-surface border border-surface-border rounded-2xl p-6 shadow-xl space-y-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Code2 className="w-5 h-5 text-cyan-400" />
            Symbol Evolution & Semantic Regression Inspector
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Track parameter signatures, behavioral contracts, and deprecation timelines for any symbol across releases.
          </p>
        </div>

        {/* Search Controls */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-surface-border">
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

          <div className="sm:col-span-2">
            <label className="block text-[11px] font-medium text-gray-400 mb-1">Symbol / API Name</label>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="e.g. assert.deepEqual"
                value={symbolQuery}
                onChange={(e) => setSymbolQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1 bg-surface-subtle border border-surface-border text-xs rounded-lg px-3 py-2 text-white font-mono placeholder-gray-500 focus:outline-none focus:border-primary"
              />
              <button
                onClick={() => handleSearch()}
                disabled={loading}
                className="px-4 py-2 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-semibold flex items-center gap-1.5 transition shadow-sm disabled:opacity-50"
              >
                <Search className="w-3.5 h-3.5" />
                <span>{loading ? 'Inspecting...' : 'Track Symbol'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Quick Suggested Symbols */}
        <div className="flex items-center gap-2 flex-wrap text-xs pt-1">
          <span className="text-gray-500 text-[11px]">Quick inspect:</span>
          {sampleSymbols.map((sym, i) => (
            <button
              key={i}
              onClick={() => {
                setSymbolQuery(sym);
                handleSearch(sym);
              }}
              className="px-2.5 py-1 rounded-md bg-surface-subtle hover:bg-surface-hover border border-surface-border text-gray-300 hover:text-white transition font-mono text-[11px]"
            >
              {sym}
            </button>
          ))}
        </div>
      </div>

      {/* History Cards */}
      {history.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            Evolution Trajectory for <span className="font-mono text-cyan-300">'{symbolQuery}'</span>
          </h3>

          <div className="grid grid-cols-1 gap-3">
            {history.map((h, idx) => (
              <div
                key={idx}
                className="bg-surface border border-surface-border rounded-2xl p-5 shadow-sm space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <VersionBadge version={h.version_tag} size="md" />
                    <span className="font-mono text-xs text-white font-bold">{h.signature}</span>
                  </div>

                  <span
                    className={`text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded ${
                      h.status === 'Supported'
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : h.status === 'Deprecated'
                        ? 'bg-amber-500/20 text-amber-400'
                        : h.status === 'Removed'
                        ? 'bg-rose-500/20 text-rose-400'
                        : 'bg-gray-500/20 text-gray-400'
                    }`}
                  >
                    {h.status}
                  </span>
                </div>

                <div className="p-3 bg-background border border-surface-border rounded-xl font-mono text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">
                  {h.documentation_excerpt}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
