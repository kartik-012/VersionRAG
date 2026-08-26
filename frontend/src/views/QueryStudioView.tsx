import React, { useState } from 'react';
import {
  Sparkles, Send, ShieldAlert, Bookmark,
  ExternalLink, Layers, CheckCircle2, AlertOctagon,
  Clock, Tag, HelpCircle, Copy, Check, Filter,
  ChevronDown, ChevronRight, ChevronUp, RefreshCw,
  Terminal, FileText, ArrowRight, ShieldCheck,
  Search, MessageSquare, Download, Share2, Compass, Cpu,
  User as UserIcon, CornerDownRight, RotateCcw, Zap
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Project, QueryResponse, Citation } from '../types';
import { VersionBadge } from '../components/VersionBadge';
import { ConfidenceBadge } from '../components/ConfidenceBadge';
import { EvidenceDrawer } from '../components/EvidenceDrawer';
import { api } from '../lib/api';

interface QueryStudioViewProps {
  project: Project | null;
  activeVersionTag: string | null;
  onOpenDocumentReader?: (versionTag: string) => void;
}

export const QueryStudioView: React.FC<QueryStudioViewProps> = ({
  project,
  activeVersionTag,
  onOpenDocumentReader,
}) => {
  const [question, setQuestion] = useState('');
  const [scope, setScope] = useState<'current' | 'specific' | 'compare' | 'all'>('specific');
  const [targetVersion, setTargetVersion] = useState(activeVersionTag || 'v15.14.0');
  const [compareVersion, setCompareVersion] = useState('v14.0.0');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<QueryResponse[]>([]);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [openReasoningMap, setOpenReasoningMap] = useState<Record<string, boolean>>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);

  const availableVersions = ['v14.0.0', 'v15.14.0', 'v16.0.0'];

  const [customTemplates, setCustomTemplates] = useState<Array<{
    category: string;
    prompt: string;
    target: string;
    archetype: string;
  }>>(() => {
    try {
      const saved = localStorage.getItem('versionrag_custom_templates');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [isAddingTemplate, setIsAddingTemplate] = useState(false);
  const [newTemplatePrompt, setNewTemplatePrompt] = useState('');
  const [newTemplateCategory, setNewTemplateCategory] = useState('Custom');

  // Dynamically generate prompts from project changes
  const dynamicPromptsFromChanges = (project?.changes_count ? [
    {
      category: 'Breaking Change',
      prompt: 'What breaking changes occurred between v14.0.0 and v15.14.0?',
      target: 'v15.14.0',
      archetype: 'VERSION_COMPARISON_QUERY',
    },
    {
      category: 'Silent AST Change',
      prompt: 'Which functions had silent behavioral modifications without changelog entries in v15.14.0?',
      target: 'v15.14.0',
      archetype: 'SILENT_CHANGE_QUERY',
    },
    {
      category: 'API Deprecation',
      prompt: 'List all APIs deprecated in v15.14.0 and their modern replacements.',
      target: 'v15.14.0',
      archetype: 'CHANGE_QUERY',
    }
  ] : []);

  const allTemplates = [
    ...customTemplates,
    ...dynamicPromptsFromChanges,
    {
      category: 'Version-Specific',
      prompt: 'Is assert.partialDeepStrictEqual() supported in version v15?',
      target: 'v15.14.0',
      archetype: 'VERSION_SPECIFIC_QUERY',
    },
    {
      category: 'Comparison',
      prompt: 'What is the difference in assert.deepEqual() prototype checking between v14 and v15?',
      target: 'v15.14.0',
      archetype: 'VERSION_COMPARISON_QUERY',
    },
    {
      category: 'Deprecation',
      prompt: 'When was assert.CallTracker deprecated and what replaces it in v15?',
      target: 'v15.14.0',
      archetype: 'CHANGE_QUERY',
    },
    {
      category: 'Silent Changes',
      prompt: 'Was legacy error formatting removed in v15 without being explicitly listed in the changelog?',
      target: 'v15.14.0',
      archetype: 'SILENT_CHANGE_QUERY',
    },
    {
      category: 'Conflict',
      prompt: 'Why does v14 state that feature X is experimental while v16 states it is stable?',
      target: 'v16.0.0',
      archetype: 'CONFLICT_QUERY',
    },
    {
      category: 'Historical',
      prompt: 'What was the return type and error contract of assert.match() in the v14 initial release?',
      target: 'v14.0.0',
      archetype: 'HISTORICAL_QUERY',
    },
  ];

  const handleSaveCustomTemplate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTemplatePrompt.trim()) return;
    const updated = [
      {
        category: newTemplateCategory,
        prompt: newTemplatePrompt.trim(),
        target: targetVersion,
        archetype: 'CUSTOM_QUERY',
      },
      ...customTemplates,
    ];
    setCustomTemplates(updated);
    localStorage.setItem('versionrag_custom_templates', JSON.stringify(updated));
    setNewTemplatePrompt('');
    setIsAddingTemplate(false);
  };

  const handleAsk = async (customPrompt?: string, customTarget?: string) => {
    const q = (customPrompt || question).trim();
    const tVer = customTarget || targetVersion;
    if (!q) return;
    if (!project) {
      setQueryError("No active project track selected. Please select a project from the left sidebar.");
      return;
    }

    setLoading(true);
    setQueryError(null);
    try {
      const res = await api.askQuestion({
        question: q,
        project_id: project.id,
        target_version: scope === 'all' ? undefined : tVer,
        scope: scope,
      });

      // Ensure res includes the question asked
      const fullRes: QueryResponse = {
        ...res,
        question: q,
      };

      setHistory((prev) => [fullRes, ...prev]);
      if (!customPrompt) setQuestion('');
    } catch (err: any) {
      setQueryError(err.message || 'Query execution encountered an issue. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const toggleReasoning = (id: string) => {
    setOpenReasoningMap((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleCopyAnswer = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="flex-1 flex overflow-hidden h-[calc(100vh-3.5rem)] bg-background">
      {/* 1. Left Rail: Templates & Archetype Navigator */}
      <aside className="w-80 border-r border-surface-border glass-panel flex flex-col shrink-0 hidden lg:flex select-none">
        {/* Rail Header */}
        <div className="p-4 border-b border-surface-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-white font-bold text-xs tracking-tight">
              <Compass className="w-4 h-4 text-primary-light" />
              <span>Query Navigator</span>
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setIsAddingTemplate(!isAddingTemplate)}
              className="text-[11px] text-primary-light hover:text-white font-semibold transition"
            >
              {isAddingTemplate ? 'Cancel' : '+ New Template'}
            </motion.button>
          </div>
          <p className="text-[11px] text-gray-400 mt-1">
            Dynamic & verified scenario prompt templates.
          </p>
        </div>

        {/* Add Template Inline Form */}
        <AnimatePresence>
          {isAddingTemplate && (
            <motion.form
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              onSubmit={handleSaveCustomTemplate}
              className="p-3 bg-surface-subtle/80 border-b border-surface-border space-y-2 text-xs overflow-hidden"
            >
              <input
                type="text"
                required
                placeholder="Enter custom prompt question..."
                value={newTemplatePrompt}
                onChange={(e) => setNewTemplatePrompt(e.target.value)}
                className="w-full bg-background border border-surface-border rounded-lg px-2.5 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-primary"
              />
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Category (e.g. My Audit)"
                  value={newTemplateCategory}
                  onChange={(e) => setNewTemplateCategory(e.target.value)}
                  className="w-1/2 bg-background border border-surface-border rounded-lg px-2 py-1 text-[11px] text-white"
                />
                <motion.button
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.97 }}
                  type="submit"
                  className="w-1/2 py-1 rounded-lg bg-primary hover:bg-primary-hover text-white text-[11px] font-semibold glow-primary"
                >
                  Save Template
                </motion.button>
              </div>
            </motion.form>
          )}
        </AnimatePresence>

        {/* Templates List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500 px-2 block font-mono">
            Available Scenarios ({allTemplates.length})
          </span>

          {allTemplates.map((tpl, i) => (
            <motion.button
              key={i}
              whileHover={{ x: 4, scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => {
                setQuestion(tpl.prompt);
                setTargetVersion(tpl.target);
                handleAsk(tpl.prompt, tpl.target);
              }}
              className="w-full text-left p-3 rounded-xl bg-surface-subtle/70 hover:bg-surface-hover border border-surface-border hover:border-primary/40 transition group space-y-1.5 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/15 text-blue-400 font-semibold border border-blue-500/30">
                  {tpl.category}
                </span>
                <VersionBadge version={tpl.target} size="sm" />
              </div>
              <p className="text-xs text-gray-300 font-medium line-clamp-2 group-hover:text-white transition">
                {tpl.prompt}
              </p>
            </motion.button>
          ))}
        </div>

        {/* Session Stats Footer */}
        <div className="p-3.5 border-t border-surface-border bg-surface-subtle/50 text-[11px] text-gray-400 flex items-center justify-between font-mono">
          <span>Queries Executed: {history.length}</span>
          <span className="text-emerald-400 flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span> Isolated Scope
          </span>
        </div>
      </aside>

      {/* 2. Center Stage: AI Reasoning Canvas */}
      <main className="flex-1 overflow-y-auto p-6 space-y-6 max-w-5xl mx-auto">
        {/* Studio Top Control Panel */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="glass-panel rounded-2xl p-5 shadow-xl space-y-4 glow-primary"
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary to-indigo-600 flex items-center justify-center text-white shadow-md shadow-primary/30">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <h1 className="text-base font-bold text-white tracking-tight">
                  Version-Aware AI Query Workbench
                </h1>
                <p className="text-xs text-gray-400">
                  Strict version-filtered vector retrieval & cross-version chronological verification.
                </p>
              </div>
            </div>

            {/* Scope Switcher */}
            <div className="flex items-center gap-1.5 bg-surface-subtle/80 p-1 rounded-xl border border-surface-border text-xs">
              <span className="text-[10px] text-gray-500 font-medium px-2 uppercase tracking-wider font-mono">
                Scope:
              </span>
              {[
                { id: 'specific', label: 'Strict Version Scope' },
                { id: 'compare', label: 'Compare Scope' },
                { id: 'all', label: 'All Releases' },
              ].map((sc) => (
                <button
                  key={sc.id}
                  onClick={() => setScope(sc.id as any)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                    scope === sc.id
                      ? 'bg-primary text-white font-semibold shadow-sm'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {sc.label}
                </button>
              ))}
            </div>
          </div>

          {/* Scope Selectors Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-surface-border text-xs">
            <div>
              <label className="block text-[11px] font-medium text-gray-400 mb-1">
                Target Version Context
              </label>
              <select
                value={targetVersion}
                onChange={(e) => setTargetVersion(e.target.value)}
                className="w-full bg-surface-subtle/80 border border-surface-border text-xs rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-primary transition"
              >
                {availableVersions.map((v) => (
                  <option key={v} value={v}>
                    {v} (Active Index)
                  </option>
                ))}
              </select>
            </div>

            {scope === 'compare' && (
              <div>
                <label className="block text-[11px] font-medium text-gray-400 mb-1">
                  Compare With Version
                </label>
                <select
                  value={compareVersion}
                  onChange={(e) => setCompareVersion(e.target.value)}
                  className="w-full bg-surface-subtle/80 border border-surface-border text-xs rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-primary transition"
                >
                  {availableVersions.map((v) => (
                    <option key={v} value={v}>
                      {v} (Comparator)
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className={scope === 'compare' ? '' : 'sm:col-span-2'}>
              <label className="block text-[11px] font-medium text-gray-400 mb-1">
                Retrieval Engine
              </label>
              <div className="w-full bg-surface-subtle/80 border border-surface-border text-xs rounded-lg px-3 py-2 text-emerald-400 font-mono flex items-center justify-between">
                <span className="flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5" /> VersionRAG Routing Engine v1.0
                </span>
                <span className="text-[10px] text-gray-500">100% Grounded</span>
              </div>
            </div>
          </div>

          {/* Interactive Multi-Line Query Input Box */}
          <div className="pt-2">
            <div className="relative rounded-2xl bg-background/80 border border-surface-border focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20 shadow-inner p-3.5 transition">
              <textarea
                rows={3}
                placeholder="Ask any version-specific question, API difference, deprecation timeline, or conflict..."
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                    handleAsk();
                  }
                }}
                className="w-full bg-transparent text-sm text-white placeholder-gray-500 focus:outline-none resize-none"
              />

              <div className="flex items-center justify-between pt-2 border-t border-surface-border/60 text-xs">
                <span className="text-[11px] text-gray-500 font-mono hidden sm:inline">
                  Press <kbd className="px-1.5 py-0.5 rounded bg-surface-subtle text-gray-300">Ctrl + Enter</kbd> to analyze
                </span>

                <div className="flex items-center gap-2 ml-auto">
                  {question.trim() && (
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => setQuestion('')}
                      className="px-3 py-1.5 text-xs text-gray-400 hover:text-white transition"
                    >
                      Clear
                    </motion.button>
                  )}
                  <motion.button
                    whileHover={{ scale: 1.04 }}
                    whileTap={{ scale: 0.96 }}
                    onClick={() => handleAsk()}
                    disabled={loading || !question.trim()}
                    className="px-5 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-primary/30 transition disabled:opacity-50 glow-primary"
                  >
                    <span>{loading ? 'Executing Retrieval...' : 'Ask VersionRAG'}</span>
                    <Send className="w-3.5 h-3.5" />
                  </motion.button>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Answer Stream */}
        <div className="space-y-8">
          {/* Error Banner */}
          <AnimatePresence>
            {queryError && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center justify-between shadow-sm glow-rose"
              >
                <div className="flex items-center gap-2.5">
                  <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
                  <span>{queryError}</span>
                </div>
                <button
                  onClick={() => handleAsk()}
                  className="px-3 py-1 bg-rose-500/20 hover:bg-rose-500/30 rounded-lg text-rose-200 text-xs font-semibold transition"
                >
                  Retry
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Active Loading Skeleton */}
          <AnimatePresence>
            {loading && (
              <motion.div
                initial={{ opacity: 0, scale: 0.97 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.97 }}
                className="glass-panel border border-primary/50 rounded-2xl p-6 shadow-xl space-y-4 glow-primary"
              >
                <div className="flex items-center justify-between pb-3 border-b border-surface-border">
                  <div className="flex items-center gap-2">
                    <RefreshCw className="w-4 h-4 text-primary-light animate-spin" />
                    <span className="text-xs font-bold text-white font-mono">
                      VERSIONRAG MULTI-VERSION REASONING ENGINE ACTIVE...
                    </span>
                  </div>
                  <span className="text-[10px] text-gray-400 font-mono">Synthesizing ground truth</span>
                </div>
                <div className="space-y-2.5 shimmer-effect rounded-lg p-2">
                  <div className="h-3.5 bg-surface-subtle/80 rounded w-3/4"></div>
                  <div className="h-3.5 bg-surface-subtle/80 rounded w-full"></div>
                  <div className="h-3.5 bg-surface-subtle/80 rounded w-5/6"></div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Chat Exchange Cards (User Question Bubble + AI Assistant Response) */}
          {history.map((resp, idx) => {
            const isReasoningOpen = openReasoningMap[resp.message_id] ?? true;

            return (
              <motion.div
                key={resp.message_id || idx}
                initial={{ opacity: 0, y: 20, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ type: 'spring', stiffness: 280, damping: 24 }}
                className="space-y-3"
              >
                {/* 1. User Question Prompt Bubble */}
                <div className="flex items-start gap-3 pl-2">
                  <div className="w-7 h-7 rounded-lg bg-blue-600/30 border border-blue-500/40 text-blue-300 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5 shadow-sm">
                    <UserIcon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 glass-panel rounded-2xl p-4 shadow-sm border border-surface-border">
                    <div className="flex items-center justify-between text-[11px] text-gray-400 mb-1">
                      <span className="font-semibold text-gray-300">You asked</span>
                      <div className="flex items-center gap-2">
                        {resp.target_version && (
                          <VersionBadge version={resp.target_version} size="sm" />
                        )}
                        <span className="font-mono text-[10px] text-gray-500">Target Release</span>
                      </div>
                    </div>
                    <p className="text-sm font-medium text-white leading-relaxed">
                      {resp.question || question}
                    </p>
                  </div>
                </div>

                {/* 2. VersionRAG Assistant Response Card */}
                <div className="flex items-start gap-3">
                  <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary to-indigo-600 text-white flex items-center justify-center font-bold text-xs shrink-0 mt-1 shadow-md shadow-primary/30">
                    <Sparkles className="w-4 h-4" />
                  </div>

                  <div className="flex-1 glass-panel rounded-2xl p-6 shadow-xl space-y-5 border border-surface-border">
                    {/* Assistant Metadata Header */}
                    <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-surface-border">
                      <div className="flex items-center gap-2.5">
                        <span className="text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-lg bg-blue-500/15 text-blue-400 border border-blue-500/30">
                          {resp.query_type.replace(/_/g, ' ').toUpperCase()}
                        </span>
                        <span className="text-xs text-gray-400 font-medium">
                          Version-Aware Grounded Response
                        </span>
                      </div>

                      <div className="flex items-center gap-3">
                        <ConfidenceBadge
                          level={resp.confidence_level}
                          score={resp.confidence_score}
                          reason={resp.confidence_reason}
                          showExplanation
                        />
                        <span className="text-[11px] font-mono text-gray-500 flex items-center gap-1">
                          <Clock className="w-3 h-3" /> {resp.latency_ms}ms
                        </span>
                      </div>
                    </div>

                    {/* Conflict Warning Callout Banner (if present) */}
                    {resp.has_conflict && resp.conflict_summary && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.97 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-start gap-3 glow-amber"
                      >
                        <ShieldAlert className="w-5 h-5 shrink-0 text-amber-400 mt-0.5" />
                        <div>
                          <h4 className="font-bold text-amber-200 mb-0.5">
                            Cross-Version Divergence Detected
                          </h4>
                          <p className="text-[11px] text-amber-200/90 leading-relaxed">
                            {resp.conflict_summary}
                          </p>
                        </div>
                      </motion.div>
                    )}

                    {/* Collapsible Chain-of-Version-Reasoning (X-Ray Thinking Trace) */}
                    <div className="rounded-xl bg-surface-subtle/80 border border-surface-border overflow-hidden text-xs">
                      <button
                        onClick={() => toggleReasoning(resp.message_id)}
                        className="w-full px-4 py-2.5 flex items-center justify-between text-gray-300 hover:text-white font-medium bg-surface-subtle/90 hover:bg-surface-hover transition"
                      >
                        <div className="flex items-center gap-2">
                          <Cpu className="w-3.5 h-3.5 text-primary" />
                          <span>Chain of Version Reasoning (4-Step Pipeline Trace)</span>
                        </div>
                        {isReasoningOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      </button>

                      <AnimatePresence>
                        {isReasoningOpen && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="p-4 border-t border-surface-border space-y-2.5 text-[11px] font-mono bg-background/90"
                          >
                            <div className="flex items-start gap-2">
                              <span className="w-4 h-4 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">
                                1
                              </span>
                              <p className="text-gray-300">
                                <strong className="text-white">Query Classification:</strong> Routed to{' '}
                                <code className="text-blue-300">{resp.query_type}</code> with high archetype affinity.
                              </p>
                            </div>

                            <div className="flex items-start gap-2">
                              <span className="w-4 h-4 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">
                                2
                              </span>
                              <p className="text-gray-300">
                                <strong className="text-white">Index Partitioning:</strong> Query filtered strictly to{' '}
                                <code className="text-emerald-300">version_tag = '{resp.target_version || 'all'}'</code>. Zero cross-version bleed.
                              </p>
                            </div>

                            <div className="flex items-start gap-2">
                              <span className="w-4 h-4 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">
                                3
                              </span>
                              <p className="text-gray-300">
                                <strong className="text-white">Temporal Diff Validation:</strong> Verified against predecessor and successor release changelogs.
                              </p>
                            </div>

                            <div className="flex items-start gap-2">
                              <span className="w-4 h-4 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">
                                4
                              </span>
                              <p className="text-gray-300">
                                <strong className="text-white">Grounding Score:</strong> Mathematical confidence of{' '}
                                <code className="text-cyan-300">{Math.round(resp.confidence_score * 100)}%</code> based on {resp.citations.length} verified evidence chunks.
                              </p>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>

                    {/* Grounded Answer Synthesis */}
                    <div className="text-sm text-gray-100 leading-relaxed whitespace-pre-wrap selection:bg-primary font-normal bg-background/60 p-5 rounded-xl border border-surface-border space-y-3">
                      {resp.answer}
                    </div>

                    {/* Interactive Verified Evidence Citations Grid */}
                    {resp.citations.length > 0 && (
                      <div className="pt-3 border-t border-surface-border space-y-2.5">
                        <div className="flex items-center justify-between">
                          <label className="text-[11px] uppercase font-bold tracking-wider text-gray-400 flex items-center gap-1.5 font-mono">
                            <Bookmark className="w-3.5 h-3.5 text-primary" />
                            Grounded Source Chunk Citations ({resp.citations.length})
                          </label>
                          <span className="text-[10px] text-gray-500 font-mono">
                            Click citation to inspect raw text & anchors
                          </span>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          {resp.citations.map((cit) => (
                            <motion.div
                              key={cit.id}
                              whileHover={{ scale: 1.02, y: -2 }}
                              whileTap={{ scale: 0.98 }}
                              onClick={() => setSelectedCitation(cit)}
                              className="p-3.5 rounded-xl bg-surface-subtle/80 border border-surface-border hover:border-primary/60 cursor-pointer transition flex flex-col justify-between space-y-2 group shadow-sm glass-card"
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-1.5 overflow-hidden">
                                  <FileText className="w-3.5 h-3.5 text-primary shrink-0" />
                                  <span className="text-white font-medium text-xs truncate">
                                    {cit.document_title}
                                  </span>
                                </div>
                                <VersionBadge version={cit.version_tag} size="sm" />
                              </div>

                              <p className="text-[11px] text-gray-400 line-clamp-2 font-mono">
                                {cit.snippet}
                              </p>

                              <div className="flex items-center justify-between pt-1 border-t border-surface-border text-[10px]">
                                <span className="text-blue-400 font-medium truncate max-w-[140px]">
                                  {cit.section_title || 'General API'}
                                </span>
                                <span className="text-emerald-400 font-mono font-bold">
                                  {Math.round(cit.similarity_score * 100)}% Match
                                </span>
                              </div>
                            </motion.div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Footer Action Bar */}
                    <div className="flex items-center justify-between pt-3 border-t border-surface-border text-xs text-gray-400">
                      <div className="flex items-center gap-2">
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => handleCopyAnswer(resp.message_id, resp.answer)}
                          className="px-3 py-1.5 rounded-lg bg-surface-subtle hover:bg-surface-hover border border-surface-border text-gray-300 hover:text-white flex items-center gap-1.5 transition"
                        >
                          {copiedId === resp.message_id ? (
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                          <span>{copiedId === resp.message_id ? 'Copied' : 'Copy Answer'}</span>
                        </motion.button>

                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => {
                            setQuestion(resp.question);
                            setTargetVersion(resp.target_version || 'v15.14.0');
                            handleAsk(resp.question, resp.target_version);
                          }}
                          className="px-3 py-1.5 rounded-lg bg-surface-subtle hover:bg-surface-hover border border-surface-border text-gray-300 hover:text-white flex items-center gap-1.5 transition"
                        >
                          <RotateCcw className="w-3.5 h-3.5" />
                          <span>Re-Analyze</span>
                        </motion.button>
                      </div>

                      <span className="font-mono text-[10px] text-gray-500">
                        Tokens: {resp.tokens_used} • Model: VersionRAG Engine
                      </span>
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}

          {history.length === 0 && !loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-16 glass-panel rounded-2xl p-8 space-y-3"
            >
              <div className="w-12 h-12 rounded-2xl bg-primary/10 text-primary-light flex items-center justify-center mx-auto shadow-sm glow-primary">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-bold text-white">Ask your first version-aware question</h3>
              <p className="text-xs text-gray-400 max-w-md mx-auto leading-relaxed">
                VersionRAG routes your query through strict version filtering, cross-version diff verification, and verifiable citation extraction.
              </p>
              <div className="pt-2 flex justify-center gap-2">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => {
                    const sample = allTemplates[0];
                    if (sample) {
                      setQuestion(sample.prompt);
                      setTargetVersion(sample.target);
                      handleAsk(sample.prompt, sample.target);
                    }
                  }}
                  className="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-semibold shadow-sm transition glow-primary"
                >
                  Run Sample Verification Query
                </motion.button>
              </div>
            </motion.div>
          )}
        </div>
      </main>

      {/* 3. Right Slideout Inspector: Raw Evidence & AST Chunk Inspector */}
      <EvidenceDrawer
        isOpen={selectedCitation !== null}
        onClose={() => setSelectedCitation(null)}
        citation={selectedCitation}
        onOpenDocumentReader={onOpenDocumentReader}
      />
    </div>
  );
};
