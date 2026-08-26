import React, { useState, useEffect } from 'react';
import {
  ArrowLeft, FileText, Bookmark, Hash,
  Search, Layers, Sparkles, GitCompare
} from 'lucide-react';
import { Document, DocumentVersion } from '../types';
import { VersionBadge } from '../components/VersionBadge';
import { api } from '../lib/api';

interface VersionDetailViewProps {
  document: Document;
  version: DocumentVersion;
  onBack: () => void;
  onCompareWithPrevious?: () => void;
  onAskAIAboutVersion?: (versionTag: string) => void;
}

export const VersionDetailView: React.FC<VersionDetailViewProps> = ({
  document: doc,
  version: initialVersion,
  onBack,
  onCompareWithPrevious,
  onAskAIAboutVersion,
}) => {
  const [fullVersion, setFullVersion] = useState<DocumentVersion>(initialVersion);
  const [loading, setLoading] = useState(false);
  const [activeSection, setActiveSection] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchDetail = async () => {
      setLoading(true);
      try {
        const res = await api.getVersionDetail(initialVersion.id);
        setFullVersion(res);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [initialVersion.id]);

  const rawLines = (fullVersion.raw_content || '').split('\n');
  
  // Extract table of contents headers
  const toc = rawLines
    .filter((line) => line.startsWith('#'))
    .map((line) => {
      const level = line.match(/^#+/)?.[0].length || 1;
      const text = line.replace(/^#+\s*/, '').trim();
      return { level, text };
    });

  return (
    <div className="h-[calc(100vh-3.5rem)] flex flex-col">
      {/* Reader Header */}
      <div className="h-14 border-b border-surface-border px-6 flex items-center justify-between bg-surface shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-surface-hover transition"
            title="Back to Documents"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-white">{doc.title}</h2>
              <VersionBadge version={fullVersion.version_tag} size="sm" active />
            </div>
            <span className="text-[11px] text-gray-400 font-mono">
              {fullVersion.source_filename || 'source.md'} • {(fullVersion.file_size_bytes / 1024).toFixed(1)} KB
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {onCompareWithPrevious && fullVersion.previous_version_id && (
            <button
              onClick={onCompareWithPrevious}
              className="px-3 py-1.5 rounded-lg bg-surface-subtle hover:bg-surface-hover border border-surface-border text-white text-xs font-medium flex items-center gap-1.5 transition"
            >
              <GitCompare className="w-3.5 h-3.5 text-purple-400" />
              Compare with Previous
            </button>
          )}

          {onAskAIAboutVersion && (
            <button
              onClick={() => onAskAIAboutVersion(fullVersion.version_tag)}
              className="px-3 py-1.5 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm shadow-primary/30 transition"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Ask AI About {fullVersion.version_tag}
            </button>
          )}
        </div>
      </div>

      {/* Reader Content Body (TOC Sidebar + Full Text Reader) */}
      <div className="flex-1 flex overflow-hidden">
        {/* Table of Contents Rail */}
        <div className="w-64 border-r border-surface-border bg-surface-subtle p-4 overflow-y-auto hidden md:block shrink-0">
          <h4 className="text-[11px] font-bold uppercase tracking-wider text-gray-400 mb-3 flex items-center gap-1.5">
            <Hash className="w-3.5 h-3.5 text-primary" />
            Table of Contents
          </h4>
          <nav className="space-y-1.5">
            {toc.map((item, idx) => (
              <a
                key={idx}
                href={`#sec-${idx}`}
                className={`block text-xs truncate transition py-1 rounded px-2 ${
                  item.level === 1
                    ? 'font-bold text-white'
                    : item.level === 2
                    ? 'text-gray-300 pl-4'
                    : 'text-gray-400 pl-6'
                } hover:bg-surface-hover hover:text-primary-light`}
              >
                {item.text}
              </a>
            ))}
          </nav>
        </div>

        {/* Full Text Pane */}
        <div className="flex-1 overflow-y-auto p-8 max-w-4xl mx-auto space-y-6">
          <div className="bg-surface border border-surface-border rounded-xl p-8 shadow-sm">
            <pre className="font-sans text-sm text-gray-200 leading-relaxed whitespace-pre-wrap selection:bg-primary font-normal">
              {fullVersion.raw_content || 'No content loaded.'}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};
