import React, { useState } from 'react';
import { GitBranch, Calendar, ShieldAlert, EyeOff, Layers, ChevronRight } from 'lucide-react';
import { Document, DocumentChange } from '../types';
import { VersionBadge } from '../components/VersionBadge';
import { ChangeBadge } from '../components/ChangeBadge';

interface TimelineViewProps {
  documents: Document[];
  changes: DocumentChange[];
}

export const TimelineView: React.FC<TimelineViewProps> = ({ documents, changes }) => {
  const [selectedDocId, setSelectedDocId] = useState<string>(documents[0]?.id || '');
  const selectedDoc = documents.find((d) => d.id === selectedDocId);

  const docChanges = changes.filter((c) => c.document_id === selectedDocId);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header & Document Picker */}
      <div className="bg-surface border border-surface-border rounded-xl p-5 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-emerald-400" />
            Version Evolution Timeline
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Chronological release trajectory and change markers across the lifecycle.
          </p>
        </div>

        <div className="w-64">
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
      </div>

      {/* Interactive Horizontal Version Sequence */}
      {selectedDoc && (
        <div className="bg-surface border border-surface-border rounded-xl p-6 shadow-sm overflow-x-auto">
          <div className="flex items-center justify-between min-w-[600px] relative">
            <div className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-0.5 bg-surface-border z-0" />
            {selectedDoc.versions.map((ver, idx) => (
              <div key={ver.id} className="relative z-10 flex flex-col items-center group">
                <div className="w-9 h-9 rounded-full bg-surface border-2 border-primary flex items-center justify-center text-xs font-mono font-bold text-white shadow-md shadow-primary/20 group-hover:scale-110 transition">
                  {idx + 1}
                </div>
                <div className="mt-2 text-center">
                  <VersionBadge version={ver.version_tag} size="sm" />
                  <span className="block text-[10px] text-gray-400 mt-0.5 font-mono">
                    {ver.source_filename || 'release'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chronological Changes Stream */}
      <div className="space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400">
          Detected Evolution Events ({docChanges.length})
        </h3>

        <div className="relative pl-6 border-l-2 border-surface-border space-y-6">
          {docChanges.map((ch) => (
            <div key={ch.id} className="relative group">
              {/* Dot marker */}
              <div className="absolute -left-[31px] top-1 w-3.5 h-3.5 rounded-full bg-primary border-2 border-background" />

              <div
                className={`p-4 rounded-xl bg-surface border shadow-sm space-y-2 transition ${
                  ch.is_breaking ? 'border-fuchsia-500/40' : ch.is_silent ? 'border-purple-500/40' : 'border-surface-border'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-bold text-white">{ch.location}</span>
                    <ChangeBadge type={ch.change_type} isBreaking={ch.is_breaking} isSilent={ch.is_silent} />
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono text-gray-400">
                      {ch.from_version_tag} → {ch.to_version_tag}
                    </span>
                  </div>
                </div>
                <p className="text-xs text-gray-300">{ch.summary}</p>
              </div>
            </div>
          ))}

          {docChanges.length === 0 && (
            <p className="text-xs text-gray-500 py-6">No historical changes recorded for this document family.</p>
          )}
        </div>
      </div>
    </div>
  );
};
