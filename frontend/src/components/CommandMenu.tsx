import React, { useState, useEffect } from 'react';
import { Search, FileText, Sparkles, BarChart3, GitCompare, GitBranch, X } from 'lucide-react';
import { ViewType } from './Sidebar';

interface CommandMenuProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (view: ViewType) => void;
}

export const CommandMenu: React.FC<CommandMenuProps> = ({ isOpen, onClose, onNavigate }) => {
  const [search, setSearch] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
        else onClose(); // parent handles toggle
      }
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const actions = [
    { label: 'Ask AI Query Studio', view: 'query' as ViewType, icon: <Sparkles className="w-4 h-4 text-blue-400" /> },
    { label: 'Compare Document Versions', view: 'diff' as ViewType, icon: <GitCompare className="w-4 h-4 text-purple-400" /> },
    { label: 'View Version Timeline', view: 'timeline' as ViewType, icon: <GitBranch className="w-4 h-4 text-emerald-400" /> },
    { label: 'Run Comparative Benchmark', view: 'evaluations' as ViewType, icon: <BarChart3 className="w-4 h-4 text-amber-400" /> },
    { label: 'Browse Documents & Chunks', view: 'documents' as ViewType, icon: <FileText className="w-4 h-4 text-cyan-400" /> },
  ];

  const filtered = actions.filter((a) => a.label.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-start justify-center pt-24 px-4">
      <div className="bg-surface border border-surface-border w-full max-w-lg rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Search Input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-surface-border">
          <Search className="w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Type a command or jump to screen..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            autoFocus
            className="w-full bg-transparent text-sm text-white placeholder-gray-500 focus:outline-none"
          />
          <button onClick={onClose} className="text-gray-500 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results */}
        <div className="p-2 max-h-80 overflow-y-auto space-y-1">
          {filtered.map((item, idx) => (
            <button
              key={idx}
              onClick={() => {
                onNavigate(item.view);
                onClose();
              }}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium text-gray-300 hover:text-white hover:bg-surface-hover transition"
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
          {filtered.length === 0 && (
            <p className="text-xs text-gray-500 text-center py-6">No matching actions found.</p>
          )}
        </div>

        <div className="px-4 py-2 bg-surface-subtle border-t border-surface-border text-[11px] text-gray-500 flex justify-between">
          <span>Navigate with arrows</span>
          <span>Esc to close</span>
        </div>
      </div>
    </div>
  );
};
