import React, { useState, useMemo } from 'react';
import {
  FileText, Plus, ExternalLink, Trash2,
  Calendar, Layers, CheckCircle2, ChevronRight,
  Search, X
} from 'lucide-react';
import { Document, DocumentVersion } from '../types';
import { VersionBadge } from '../components/VersionBadge';

interface DocumentsViewProps {
  documents: Document[];
  onOpenUploadModal: () => void;
  onSelectVersion: (doc: Document, version: DocumentVersion) => void;
  onDeleteDocument: (docId: string) => void;
}

export const DocumentsView: React.FC<DocumentsViewProps> = ({
  documents,
  onOpenUploadModal,
  onSelectVersion,
  onDeleteDocument,
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredDocs = useMemo(() => {
    if (!searchQuery.trim()) return documents;
    const q = searchQuery.toLowerCase();
    return documents.filter(
      (doc) =>
        doc.title.toLowerCase().includes(q) ||
        (doc.description && doc.description.toLowerCase().includes(q))
    );
  }, [documents, searchQuery]);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Document Families & Versions</h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Manage evolving documents, inspect version hierarchies, and upload new releases.
          </p>
        </div>
        <button
          onClick={onOpenUploadModal}
          className="px-4 py-2 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-semibold shadow-md shadow-primary/30 flex items-center gap-1.5 transition"
        >
          <Plus className="w-3.5 h-3.5" />
          Upload Document Version
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="relative max-w-md">
        <Search className="w-4 h-4 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Filter document families..."
          aria-label="Filter document families"
          className="w-full bg-surface-subtle border border-surface-border rounded-xl pl-9 pr-9 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-primary transition"
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery('')}
            aria-label="Clear document filter"
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Document Family Cards Grid */}
      <div className="grid grid-cols-1 gap-5">
        {filteredDocs.map((doc) => (
          <div
            key={doc.id}
            className="bg-surface border border-surface-border rounded-xl p-5 shadow-sm space-y-4 hover:border-gray-700 transition"
          >
            {/* Top Info */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-surface-border">
              <div>
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-blue-400" />
                  <h3 className="text-sm font-bold text-white">{doc.title}</h3>
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-surface-subtle border border-surface-border text-gray-400">
                    {doc.doc_type}
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-1">{doc.description || 'No description provided.'}</p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => onDeleteDocument(doc.id)}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-rose-400 hover:bg-surface-hover transition"
                  title="Delete Document Family"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Nested Version Cards */}
            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-gray-400 mb-2">
                Version Timeline Releases ({doc.versions.length})
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {doc.versions.map((ver) => (
                  <div
                    key={ver.id}
                    onClick={() => onSelectVersion(doc, ver)}
                    className="p-3.5 bg-surface-subtle border border-surface-border hover:border-primary/50 rounded-lg cursor-pointer transition group shadow-sm flex flex-col justify-between space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <VersionBadge version={ver.version_tag} size="md" />
                      <span className="text-[10px] text-emerald-400 flex items-center gap-1 font-medium">
                        <CheckCircle2 className="w-3 h-3" /> Ready
                      </span>
                    </div>

                    <div className="text-[11px] text-gray-400 space-y-1">
                      <div className="flex items-center justify-between">
                        <span>File:</span>
                        <span className="font-mono text-gray-300 truncate max-w-[120px]">
                          {ver.source_filename || 'source.md'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>Size:</span>
                        <span className="font-mono text-gray-300">{(ver.file_size_bytes / 1024).toFixed(1)} KB</span>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-surface-border flex items-center justify-between text-[11px] text-primary-light font-medium group-hover:text-white transition">
                      <span>Open Document Reader</span>
                      <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}

        {documents.length > 0 && filteredDocs.length === 0 && (
          <div className="text-center py-12 bg-surface/50 border border-surface-border rounded-xl p-6">
            <p className="text-xs text-gray-400">
              No document families match "<span className="text-white font-medium">{searchQuery}</span>".
            </p>
            <button
              onClick={() => setSearchQuery('')}
              className="mt-2 text-xs text-primary-light hover:underline font-medium"
            >
              Clear search filter
            </button>
          </div>
        )}

        {documents.length === 0 && (
          <div className="text-center py-16 bg-surface border border-surface-border rounded-xl p-8">
            <FileText className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <h3 className="text-sm font-semibold text-white">No documents uploaded yet</h3>
            <p className="text-xs text-gray-400 mt-1 mb-4">
              Upload your first evolving document to begin version-aware analysis.
            </p>
            <button
              onClick={onOpenUploadModal}
              className="px-4 py-2 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-semibold shadow-md transition"
            >
              Upload Document
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
