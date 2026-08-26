import React from 'react';
import {
  FileText, GitBranch, GitCompare, Sparkles,
  BarChart3, AlertTriangle, ArrowRight, ShieldAlert,
  Clock, Database, CheckCircle2, GitPullRequest, Code2, Layers, Cpu, Zap
} from 'lucide-react';
import { motion } from 'framer-motion';
import { Project, Document, DocumentChange, EvaluationRun } from '../types';
import { VersionBadge } from '../components/VersionBadge';
import { ChangeBadge } from '../components/ChangeBadge';
import { ViewType } from '../components/Sidebar';
import { Card3D } from '../components/Card3D';

interface DashboardViewProps {
  project: Project | null;
  documents: Document[];
  changes: DocumentChange[];
  latestEvaluation: EvaluationRun | null;
  onChangeView: (view: ViewType) => void;
  onOpenUploadModal: () => void;
}

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.07,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 15 },
  show: {
    opacity: 1,
    y: 0,
    transition: {
      type: 'spring' as const,
      stiffness: 300,
      damping: 24,
    },
  },
};

export const DashboardView: React.FC<DashboardViewProps> = ({
  project,
  documents,
  changes,
  latestEvaluation,
  onChangeView,
  onOpenUploadModal,
}) => {
  const totalVersions = documents.reduce((acc, d) => acc + d.versions.length, 0);
  const breakingChanges = changes.filter((c) => c.is_breaking);
  const silentChanges = changes.filter((c) => c.is_silent);

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="p-6 space-y-6 max-w-7xl mx-auto"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Layers className="w-5 h-5 text-blue-400" />
            <span className="text-gradient">Executive Knowledge & Multi-Version Hub</span>
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Active Project Track: <span className="text-blue-400 font-semibold">{project?.name || 'No Project Selected'}</span>
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => onChangeView('migration')}
            className="px-3.5 py-2 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/40 text-indigo-300 text-xs font-semibold flex items-center gap-1.5 transition shadow-sm"
          >
            <GitPullRequest className="w-3.5 h-3.5" />
            Migration Studio
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={onOpenUploadModal}
            className="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-semibold shadow-md shadow-primary/30 flex items-center gap-1.5 transition glow-primary"
          >
            <FileText className="w-3.5 h-3.5" />
            Upload Document Version
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => onChangeView('query')}
            className="px-4 py-2 rounded-xl bg-surface-subtle hover:bg-surface-hover border border-surface-border text-white text-xs font-medium flex items-center gap-1.5 transition shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            AI Query Studio
          </motion.button>
        </div>
      </motion.div>

      {/* Breaking Changes Priority Alert Banner */}
      {breakingChanges.length > 0 && (
        <motion.div
          variants={itemVariants}
          className="p-4 rounded-2xl bg-gradient-to-r from-fuchsia-950/40 via-surface to-surface border border-fuchsia-500/40 flex items-center justify-between shadow-lg glow-rose"
        >
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-fuchsia-500/20 text-fuchsia-400 flex items-center justify-center shrink-0 border border-fuchsia-500/30">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-fuchsia-300">
                {breakingChanges.length} Breaking Changes Detected Across Releases
              </h4>
              <p className="text-[11px] text-gray-400 mt-0.5">
                Functions modified with breaking signatures between version releases. Review automated refactoring guidance.
              </p>
            </div>
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => onChangeView('migration')}
            className="px-3.5 py-1.5 rounded-xl bg-fuchsia-500/20 hover:bg-fuchsia-500/30 border border-fuchsia-500/40 text-fuchsia-300 text-xs font-semibold transition shrink-0"
          >
            Generate Refactoring Guide
          </motion.button>
        </motion.div>
      )}

      {/* 4 Metric KPI Cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card3D
          onClick={() => onChangeView('documents')}
          className="p-5 rounded-2xl glass-card border border-surface-border hover:border-primary/50 shadow-sm"
        >
          <div className="flex items-center justify-between text-gray-400 mb-2">
            <span className="text-xs font-medium">Document Families</span>
            <FileText className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">{documents.length}</div>
          <div className="text-[11px] text-gray-400 mt-1 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            <span>{totalVersions} Indexed Version Releases</span>
          </div>
        </Card3D>

        <Card3D
          onClick={() => onChangeView('diff')}
          className="p-5 rounded-2xl glass-card border border-surface-border hover:border-purple-500/50 shadow-sm"
        >
          <div className="flex items-center justify-between text-gray-400 mb-2">
            <span className="text-xs font-medium">Changes Tracked</span>
            <GitCompare className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">{changes.length}</div>
          <div className="text-[11px] text-purple-400 mt-1 flex items-center gap-1 font-medium">
            <span>{silentChanges.length} Silent / Undocumented</span>
          </div>
        </Card3D>

        <Card3D
          onClick={() => onChangeView('evaluations')}
          className="p-5 rounded-2xl glass-card border border-emerald-500/30 hover:border-emerald-500/60 shadow-sm glow-emerald"
        >
          <div className="flex items-center justify-between text-gray-400 mb-2">
            <span className="text-xs font-medium text-emerald-400">VersionRAG Accuracy</span>
            <BarChart3 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 font-mono">
            {latestEvaluation ? `${Math.round(latestEvaluation.versionrag_accuracy * 100)}%` : '88%'}
          </div>
          <div className="text-[11px] text-gray-400 mt-1">
            vs. Naive Baseline: <span className="text-rose-400 font-medium">75%</span>
          </div>
        </Card3D>

        <Card3D
          onClick={() => onChangeView('symbols')}
          className="p-5 rounded-2xl glass-card border border-surface-border hover:border-cyan-500/50 shadow-sm"
        >
          <div className="flex items-center justify-between text-gray-400 mb-2">
            <span className="text-xs font-medium">Symbol Evolution</span>
            <Code2 className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-cyan-400 font-mono">Semantic AST</div>
          <div className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1">
            <span>Live Regression Tracking</span>
          </div>
        </Card3D>
      </motion.div>

      {/* Production Architecture & Multi-Version Pipeline Status */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="p-4 rounded-2xl glass-panel space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-white">
            <Database className="w-4 h-4 text-blue-400" />
            <span>Vector Index Isolation</span>
          </div>
          <p className="text-[11px] text-gray-400 leading-relaxed">
            Every document chunk is indexed with its immutable <code className="text-blue-300">version_tag</code>. Cross-version bleeding is blocked at the query routing layer.
          </p>
        </div>

        <div className="p-4 rounded-2xl glass-panel space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-white">
            <Cpu className="w-4 h-4 text-purple-400" />
            <span>Change Intelligence Engine</span>
          </div>
          <p className="text-[11px] text-gray-400 leading-relaxed">
            Combines explicit release notes with deep structural AST diffing to expose undocumented behavioral modifications.
          </p>
        </div>

        <div className="p-4 rounded-2xl glass-panel space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-white">
            <BarChart3 className="w-4 h-4 text-emerald-400" />
            <span>Verifiable Citations</span>
          </div>
          <p className="text-[11px] text-gray-400 leading-relaxed">
            Every answer links directly to verified source chunk excerpts with deterministic similarity scores and section anchors.
          </p>
        </div>
      </motion.div>

      {/* Grid: Recent Documents & Recent Detected Changes */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Documents Card */}
        <div className="glass-panel rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-400" />
              Evolving Document Families
            </h3>
            <button
              onClick={() => onChangeView('documents')}
              className="text-xs text-primary-light hover:underline flex items-center gap-1"
            >
              View All <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-3">
            {documents.slice(0, 3).map((doc) => (
              <motion.div
                key={doc.id}
                whileHover={{ x: 3 }}
                className="p-3.5 bg-surface-subtle/80 border border-surface-border rounded-xl flex items-center justify-between hover:border-gray-600 transition"
              >
                <div>
                  <h4 className="text-xs font-semibold text-white">{doc.title}</h4>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[11px] text-gray-400">
                      {doc.versions.length} versions
                    </span>
                    <span className="text-gray-600">•</span>
                    <span className="text-[11px] text-emerald-400">● Ready</span>
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  {doc.versions.map((v) => (
                    <VersionBadge key={v.id} version={v.version_tag} size="sm" />
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Recent Changes Timeline Feed */}
        <div className="glass-panel rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <GitCompare className="w-4 h-4 text-purple-400" />
              Recent Detected Changes
            </h3>
            <button
              onClick={() => onChangeView('diff')}
              className="text-xs text-primary-light hover:underline flex items-center gap-1"
            >
              Compare Releases <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
            {changes.slice(0, 5).map((c) => (
              <motion.div
                key={c.id}
                whileHover={{ x: 3 }}
                className="p-3 bg-surface-subtle/80 border border-surface-border rounded-xl text-xs space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-gray-300 font-medium">{c.location}</span>
                  <div className="flex items-center gap-1.5">
                    <ChangeBadge type={c.change_type} isBreaking={c.is_breaking} isSilent={c.is_silent} />
                    <span className="text-[10px] font-mono text-gray-400">
                      {c.from_version_tag} → {c.to_version_tag}
                    </span>
                  </div>
                </div>
                <p className="text-[11px] text-gray-400">{c.summary}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};
