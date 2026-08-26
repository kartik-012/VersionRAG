import React from 'react';
import { X, FileText, ExternalLink, Bookmark, Check } from 'lucide-react';
import { Citation } from '../types';
import { VersionBadge } from './VersionBadge';

interface EvidenceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  citation: Citation | null;
  onOpenDocumentReader?: (versionTag: string) => void;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({
  isOpen,
  onClose,
  citation,
  onOpenDocumentReader,
}) => {
  if (!isOpen || !citation) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-96 bg-surface border-l border-surface-border shadow-2xl z-40 flex flex-col animate-in slide-in-from-right duration-200">
      {/* Drawer Header */}
      <div className="p-4 border-b border-surface-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bookmark className="w-4 h-4 text-primary" />
          <h3 className="text-sm font-semibold text-white">Evidence Inspector</h3>
        </div>
        <button onClick={onClose} className="p-1 rounded text-gray-400 hover:text-white">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Drawer Body */}
      <div className="p-4 flex-1 overflow-y-auto space-y-4 text-xs">
        {/* Source Document & Version */}
        <div className="bg-surface-subtle p-3 rounded-lg border border-surface-border space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-gray-400">Document</span>
            <span className="text-white font-medium">{citation.document_title}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-400">Version Tag</span>
            <VersionBadge version={citation.version_tag} size="sm" />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-400">Section</span>
            <span className="text-blue-400 font-medium">{citation.section_title || 'General'}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-400">Similarity Score</span>
            <span className="font-mono text-emerald-400">{Math.round(citation.similarity_score * 100)}% Match</span>
          </div>
        </div>

        {/* Chunk Content Excerpt */}
        <div>
          <label className="block text-gray-400 font-medium mb-1.5 uppercase text-[10px] tracking-wider">
            Verified Source Chunk Text
          </label>
          <div className="bg-background border border-surface-border rounded-lg p-3 text-gray-200 font-mono text-[11px] leading-relaxed whitespace-pre-wrap selection:bg-primary">
            {citation.snippet}
          </div>
        </div>

        {/* Action: Open in Document Reader */}
        {onOpenDocumentReader && (
          <button
            onClick={() => {
              onOpenDocumentReader(citation.version_tag);
              onClose();
            }}
            className="w-full py-2.5 rounded-lg bg-primary hover:bg-primary-hover text-white font-medium flex items-center justify-center gap-2 transition"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            Open in Document Reader
          </button>
        )}
      </div>
    </div>
  );
};
