import React from 'react';
import {
  LayoutDashboard, FolderGit2, FileText, GitCompare,
  GitBranch, Sparkles, BarChart3, Settings, Plus,
  Database, Zap
} from 'lucide-react';
import { motion } from 'framer-motion';
import { Workspace, Project } from '../types';

export type ViewType =
  | 'dashboard'
  | 'documents'
  | 'diff'
  | 'migration'
  | 'symbols'
  | 'timeline'
  | 'query'
  | 'evaluations'
  | 'settings';

interface SidebarProps {
  currentView: ViewType;
  onChangeView: (view: ViewType) => void;
  workspaces: Workspace[];
  currentWorkspace: Workspace | null;
  onSelectWorkspace: (ws: Workspace) => void;
  onNewWorkspace: () => void;
  projects: Project[];
  currentProject: Project | null;
  onSelectProject: (proj: Project) => void;
  onNewProject: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentView,
  onChangeView,
  workspaces,
  currentWorkspace,
  onSelectWorkspace,
  onNewWorkspace,
  projects,
  currentProject,
  onSelectProject,
  onNewProject,
}) => {
  const navItems: { id: ViewType; label: string; icon: React.ReactNode; badge?: number; isNew?: boolean; color: string }[] = [
    { id: 'dashboard', label: 'Executive Dashboard', icon: <LayoutDashboard className="w-4 h-4" />, color: 'text-blue-400' },
    { id: 'documents', label: 'Documents & Versions', icon: <FileText className="w-4 h-4" />, badge: currentProject?.documents_count, color: 'text-emerald-400' },
    { id: 'diff', label: 'Version Comparison', icon: <GitCompare className="w-4 h-4" />, badge: currentProject?.changes_count, color: 'text-amber-400' },
    { id: 'migration', label: 'Migration Synthesizer', icon: <FolderGit2 className="w-4 h-4" />, isNew: true, color: 'text-indigo-400' },
    { id: 'symbols', label: 'Symbol Evolution', icon: <GitBranch className="w-4 h-4" />, isNew: true, color: 'text-cyan-400' },
    { id: 'timeline', label: 'Evolution Timeline', icon: <GitBranch className="w-4 h-4" />, color: 'text-purple-400' },
    { id: 'query', label: 'AI Query Studio', icon: <Sparkles className="w-4 h-4" />, color: 'text-blue-400' },
    { id: 'evaluations', label: 'Evaluations & Benchmark', icon: <BarChart3 className="w-4 h-4" />, color: 'text-emerald-400' },
    { id: 'settings', label: 'Workspace & RBAC', icon: <Settings className="w-4 h-4" />, color: 'text-gray-400' },
  ];

  return (
    <aside className="w-64 border-r border-surface-border glass-panel flex flex-col h-[calc(100vh-3.5rem)] shrink-0 select-none z-20">
      {/* Workspace Switcher */}
      <div className="p-3.5 border-b border-surface-border">
        <div className="flex items-center justify-between mb-1.5 px-1">
          <span className="text-[10px] font-bold tracking-wider uppercase text-gray-500 font-mono">Workspace</span>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onNewWorkspace}
            className="text-[11px] text-primary-light hover:text-white flex items-center gap-0.5 font-medium transition"
            title="Create Workspace"
          >
            <Plus className="w-3 h-3" /> New
          </motion.button>
        </div>
        <select
          value={currentWorkspace?.id || ''}
          onChange={(e) => {
            const ws = workspaces.find((w) => w.id === e.target.value);
            if (ws) onSelectWorkspace(ws);
          }}
          className="w-full bg-surface-subtle/80 border border-surface-border text-xs rounded-xl px-3 py-2 text-gray-200 focus:outline-none focus:border-primary font-medium transition shadow-sm hover:border-surface-border/80"
        >
          {workspaces.map((w) => (
            <option key={w.id} value={w.id}>
              {w.name}
            </option>
          ))}
        </select>
      </div>

      {/* Project Switcher */}
      <div className="p-3.5 border-b border-surface-border">
        <div className="flex items-center justify-between mb-1.5 px-1">
          <span className="text-[10px] font-bold tracking-wider uppercase text-gray-500 font-mono">Project Track</span>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onNewProject}
            className="text-[11px] text-primary-light hover:text-white flex items-center gap-0.5 font-medium transition"
            title="Create Project"
          >
            <Plus className="w-3 h-3" /> New
          </motion.button>
        </div>
        <select
          value={currentProject?.id || ''}
          onChange={(e) => {
            const p = projects.find((proj) => proj.id === e.target.value);
            if (p) onSelectProject(p);
          }}
          className="w-full bg-surface-subtle/80 border border-surface-border text-xs rounded-xl px-3 py-2 text-blue-300 focus:outline-none focus:border-primary font-medium transition shadow-sm hover:border-surface-border/80"
        >
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 p-3 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => {
          const active = currentView === item.id;
          return (
            <motion.button
              key={item.id}
              whileHover={{ x: 4, transition: { duration: 0.15 } }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onChangeView(item.id)}
              className={`w-full relative flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-medium transition-colors group ${
                active
                  ? 'text-white font-semibold shadow-md shadow-primary/25'
                  : 'text-gray-400 hover:text-gray-100 hover:bg-surface-hover/80'
              }`}
            >
              {active && (
                <motion.div
                  layoutId="activeSidebarIndicator"
                  className="absolute inset-0 bg-primary rounded-xl z-0"
                  transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                />
              )}

              <div className="relative z-10 flex items-center gap-3">
                <span className={`${active ? 'text-white' : item.color} transition-transform group-hover:scale-110`}>
                  {item.icon}
                </span>
                <span className="truncate">{item.label}</span>
              </div>

              <div className="relative z-10 flex items-center gap-1.5">
                {item.isNew && (
                  <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 uppercase">
                    PRO
                  </span>
                )}
                {item.badge !== undefined && item.badge > 0 && (
                  <span
                    className={`text-[10px] font-mono px-1.5 py-0.5 rounded-full font-bold ${
                      active ? 'bg-white/20 text-white' : 'bg-surface-subtle text-gray-400 border border-surface-border'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </div>
            </motion.button>
          );
        })}
      </nav>

      {/* Architecture Footer Status with 2D pulse */}
      <div className="p-3.5 border-t border-surface-border bg-surface-subtle/40 text-[11px] text-gray-400 flex items-center justify-between font-mono">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-gray-300">pgvector v1.0</span>
        </div>
        <span className="text-emerald-400 font-bold flex items-center gap-1">
          <Zap className="w-3 h-3" /> ONLINE
        </span>
      </div>
    </aside>
  );
};
