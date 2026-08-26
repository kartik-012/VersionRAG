import React, { useState, useRef, useEffect } from 'react';
import {
  Layers, Search, Bell, User as UserIcon,
  ChevronRight, ChevronDown, LogOut, ShieldCheck,
  Database, Zap, Plus, Check, Settings, Activity,
  Sparkles, FileText, GitCompare, GitPullRequest,
  AlertTriangle, Key, ExternalLink, Command
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Workspace, Project } from '../types';
import { VersionBadge } from './VersionBadge';
import { ViewType } from './Sidebar';

interface NavbarProps {
  user: User | null;
  currentWorkspace: Workspace | null;
  workspaces?: Workspace[];
  onSelectWorkspace?: (ws: Workspace) => void;
  onNewWorkspace?: () => void;
  currentProject: Project | null;
  projects?: Project[];
  onSelectProject?: (proj: Project) => void;
  onNewProject?: () => void;
  activeVersionTag: string | null;
  onOpenCommandMenu: () => void;
  onOpenUploadModal?: () => void;
  onNavigate?: (view: ViewType) => void;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  user,
  currentWorkspace,
  workspaces = [],
  onSelectWorkspace,
  onNewWorkspace,
  currentProject,
  projects = [],
  onSelectProject,
  onNewProject,
  activeVersionTag,
  onOpenCommandMenu,
  onOpenUploadModal,
  onNavigate,
  onLogout,
}) => {
  const [isWorkspaceMenuOpen, setIsWorkspaceMenuOpen] = useState(false);
  const [isProjectMenuOpen, setIsProjectMenuOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isTelemetryHovered, setIsTelemetryHovered] = useState(false);

  const workspaceRef = useRef<HTMLDivElement>(null);
  const projectRef = useRef<HTMLDivElement>(null);
  const notificationRef = useRef<HTMLDivElement>(null);
  const userRef = useRef<HTMLDivElement>(null);

  // Close menus on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (workspaceRef.current && !workspaceRef.current.contains(event.target as Node)) {
        setIsWorkspaceMenuOpen(false);
      }
      if (projectRef.current && !projectRef.current.contains(event.target as Node)) {
        setIsProjectMenuOpen(false);
      }
      if (notificationRef.current && !notificationRef.current.contains(event.target as Node)) {
        setIsNotificationsOpen(false);
      }
      if (userRef.current && !userRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const notifications = [
    {
      id: '1',
      title: 'Breaking Changes Detected',
      desc: 'assert.deepEqual() prototype checking contract updated in v15.14.0',
      time: 'Just now',
      type: 'warning',
      icon: <AlertTriangle className="w-4 h-4 text-amber-400" />,
    },
    {
      id: '2',
      title: 'Silent Removal Identified',
      desc: 'Legacy error format headers silently omitted in v15 documentation',
      time: '5m ago',
      type: 'info',
      icon: <Sparkles className="w-4 h-4 text-purple-400" />,
    },
    {
      id: '3',
      title: 'Benchmark Run Verified',
      desc: 'Standard eval suite: VersionRAG achieved 88% accuracy vs 75% baseline',
      time: '12m ago',
      type: 'success',
      icon: <Check className="w-4 h-4 text-emerald-400" />,
    },
  ];

  return (
    <header className="h-14 border-b border-surface-border glass-panel px-4 flex items-center justify-between sticky top-0 z-40 select-none">
      {/* 1. Left: Interactive Mission Control Breadcrumb Popovers */}
      <div className="flex items-center gap-1.5 text-xs text-gray-400">
        {/* Brand Logo */}
        <motion.div
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => onNavigate && onNavigate('dashboard')}
          className="flex items-center gap-2 font-semibold text-white cursor-pointer pr-1"
        >
          <div className="w-7 h-7 rounded-xl bg-gradient-to-br from-primary via-indigo-600 to-cyan-500 flex items-center justify-center text-white shadow-md shadow-primary/30 glow-primary">
            <Layers className="w-4 h-4" />
          </div>
          <span className="text-gradient font-bold tracking-tight text-sm hidden sm:inline">
            VersionRAG
          </span>
        </motion.div>

        <ChevronRight className="w-3.5 h-3.5 text-gray-600 shrink-0" />

        {/* Workspace Dropdown Trigger */}
        <div className="relative" ref={workspaceRef}>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setIsWorkspaceMenuOpen(!isWorkspaceMenuOpen)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-surface-subtle/80 hover:bg-surface-hover border border-surface-border text-gray-200 font-medium transition"
          >
            <span className="truncate max-w-[130px] font-semibold">
              {currentWorkspace?.name || 'Workspace'}
            </span>
            <ChevronDown className="w-3 h-3 text-gray-400" />
          </motion.button>

          {/* Workspace Dropdown Popover */}
          <AnimatePresence>
            {isWorkspaceMenuOpen && (
              <motion.div
                initial={{ opacity: 0, y: 8, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 8, scale: 0.95 }}
                transition={{ duration: 0.15 }}
                className="absolute left-0 mt-2 w-64 glass-panel rounded-2xl shadow-2xl p-2 z-50 border border-surface-border glow-primary"
              >
                <div className="px-3 py-1.5 text-[10px] font-mono font-bold uppercase tracking-wider text-gray-500">
                  Switch Workspace
                </div>
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {workspaces.map((ws) => (
                    <button
                      key={ws.id}
                      onClick={() => {
                        if (onSelectWorkspace) onSelectWorkspace(ws);
                        setIsWorkspaceMenuOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 rounded-xl text-xs flex items-center justify-between hover:bg-surface-hover text-gray-200 transition"
                    >
                      <span className="truncate font-medium">{ws.name}</span>
                      {ws.id === currentWorkspace?.id && (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      )}
                    </button>
                  ))}
                </div>
                {onNewWorkspace && (
                  <div className="pt-2 mt-1 border-t border-surface-border">
                    <button
                      onClick={() => {
                        onNewWorkspace();
                        setIsWorkspaceMenuOpen(false);
                      }}
                      className="w-full text-left px-3 py-1.5 rounded-lg text-xs text-primary-light hover:text-white hover:bg-primary/20 flex items-center gap-1.5 font-medium transition"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Create New Workspace</span>
                    </button>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <ChevronRight className="w-3.5 h-3.5 text-gray-600 shrink-0" />

        {/* Project Track Dropdown Trigger */}
        <div className="relative" ref={projectRef}>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setIsProjectMenuOpen(!isProjectMenuOpen)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-surface-subtle/80 hover:bg-surface-hover border border-surface-border text-blue-300 font-medium transition"
          >
            <span className="truncate max-w-[150px] font-semibold text-blue-400">
              {currentProject?.name || 'Project Track'}
            </span>
            <ChevronDown className="w-3 h-3 text-gray-400" />
          </motion.button>

          {/* Project Dropdown Popover */}
          <AnimatePresence>
            {isProjectMenuOpen && (
              <motion.div
                initial={{ opacity: 0, y: 8, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 8, scale: 0.95 }}
                transition={{ duration: 0.15 }}
                className="absolute left-0 mt-2 w-72 glass-panel rounded-2xl shadow-2xl p-2 z-50 border border-surface-border glow-primary"
              >
                <div className="px-3 py-1.5 text-[10px] font-mono font-bold uppercase tracking-wider text-gray-500">
                  Select Project Track
                </div>
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {projects.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => {
                        if (onSelectProject) onSelectProject(p);
                        setIsProjectMenuOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 rounded-xl text-xs flex items-center justify-between hover:bg-surface-hover text-gray-200 transition"
                    >
                      <div className="overflow-hidden pr-2">
                        <div className="font-medium text-white truncate">{p.name}</div>
                        <div className="text-[10px] text-gray-400 font-mono">
                          {p.documents_count} docs • {p.changes_count} changes
                        </div>
                      </div>
                      {p.id === currentProject?.id && (
                        <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      )}
                    </button>
                  ))}
                </div>
                {onNewProject && (
                  <div className="pt-2 mt-1 border-t border-surface-border">
                    <button
                      onClick={() => {
                        onNewProject();
                        setIsProjectMenuOpen(false);
                      }}
                      className="w-full text-left px-3 py-1.5 rounded-lg text-xs text-primary-light hover:text-white hover:bg-primary/20 flex items-center gap-1.5 font-medium transition"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Add New Project Track</span>
                    </button>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Global Active Version Context Pill */}
        {activeVersionTag && (
          <div className="hidden lg:flex items-center gap-1.5 pl-2">
            <VersionBadge version={activeVersionTag} size="sm" active />
          </div>
        )}
      </div>

      {/* 2. Center/Right: Omnisearch, Telemetry, Notifications & Executive Profile */}
      <div className="flex items-center gap-3">
        {/* Real-Time Telemetry Beacon */}
        <div
          className="relative hidden xl:block"
          onMouseEnter={() => setIsTelemetryHovered(true)}
          onMouseLeave={() => setIsTelemetryHovered(false)}
        >
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-xl bg-surface-subtle/70 border border-surface-border text-[11px] font-mono text-gray-300 cursor-help">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span>pgvector: 15 chunks (0% Bleed)</span>
          </div>

          {/* Telemetry Popover */}
          <AnimatePresence>
            {isTelemetryHovered && (
              <motion.div
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 5 }}
                className="absolute right-0 mt-2 w-64 glass-panel rounded-2xl p-3.5 text-xs shadow-2xl border border-surface-border space-y-2 z-50 pointer-events-none"
              >
                <div className="flex items-center justify-between text-[11px] font-bold text-emerald-400 font-mono pb-1 border-b border-surface-border">
                  <span>SYSTEM TELEMETRY</span>
                  <span className="text-[10px] text-gray-500">REALTIME</span>
                </div>
                <div className="space-y-1 font-mono text-[11px] text-gray-300">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Partition Engine:</span>
                    <span className="text-white">Strict SQL Filter</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Vector Index:</span>
                    <span className="text-blue-300">HNSW 1536-dim</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Avg Retrieval:</span>
                    <span className="text-emerald-300">5.4ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Contamination:</span>
                    <span className="text-emerald-400 font-bold">0.0% (Verified)</span>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Global Omnisearch Trigger */}
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onOpenCommandMenu}
          className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl bg-surface-subtle/80 border border-surface-border hover:border-primary/50 text-xs text-gray-400 hover:text-white transition shadow-sm"
        >
          <Search className="w-3.5 h-3.5 text-gray-400" />
          <span className="hidden md:inline">Jump to document, diff, query...</span>
          <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-surface-border/80 text-[10px] font-mono text-gray-300">
            <Command className="w-2.5 h-2.5" /> K
          </kbd>
        </motion.button>

        {/* Upload Version Quick Action */}
        {onOpenUploadModal && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onOpenUploadModal}
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-primary/20 hover:bg-primary/30 border border-primary/40 text-primary-light hover:text-white text-xs font-semibold transition glow-primary"
            title="Upload Document Version"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Upload</span>
          </motion.button>
        )}

        {/* Notification Bell Center */}
        <div className="relative" ref={notificationRef}>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setIsNotificationsOpen(!isNotificationsOpen)}
            className="p-2 rounded-xl bg-surface-subtle/80 hover:bg-surface-hover border border-surface-border text-gray-400 hover:text-white relative transition"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-background animate-pulse" />
          </motion.button>

          {/* Notifications Popover */}
          <AnimatePresence>
            {isNotificationsOpen && (
              <motion.div
                initial={{ opacity: 0, y: 8, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 8, scale: 0.95 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 mt-2 w-80 glass-panel rounded-2xl shadow-2xl p-4 z-50 border border-surface-border space-y-3 glow-primary"
              >
                <div className="flex items-center justify-between pb-2 border-b border-surface-border">
                  <div className="flex items-center gap-1.5 font-bold text-xs text-white">
                    <Activity className="w-4 h-4 text-primary-light" />
                    <span>Evolution Activity Center</span>
                  </div>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-primary/20 text-primary-light font-semibold">
                    3 New
                  </span>
                </div>

                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {notifications.map((n) => (
                    <div
                      key={n.id}
                      className="p-2.5 rounded-xl bg-surface-subtle/80 hover:bg-surface-hover border border-surface-border text-xs space-y-1 transition cursor-pointer"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5 font-semibold text-white">
                          {n.icon}
                          <span className="truncate">{n.title}</span>
                        </div>
                        <span className="text-[10px] text-gray-500 font-mono">{n.time}</span>
                      </div>
                      <p className="text-[11px] text-gray-400 leading-relaxed">{n.desc}</p>
                    </div>
                  ))}
                </div>

                <div className="pt-2 border-t border-surface-border flex justify-between text-[11px]">
                  <button
                    onClick={() => {
                      if (onNavigate) onNavigate('timeline');
                      setIsNotificationsOpen(false);
                    }}
                    className="text-primary-light hover:underline font-medium"
                  >
                    View All Activity Timeline →
                  </button>
                  <button
                    onClick={() => setIsNotificationsOpen(false)}
                    className="text-gray-500 hover:text-white"
                  >
                    Dismiss
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Executive User Profile Manager */}
        {user && (
          <div className="relative" ref={userRef}>
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="flex items-center gap-2 pl-2 pr-2.5 py-1 rounded-xl bg-surface-subtle/80 hover:bg-surface-hover border border-surface-border text-xs text-gray-300 transition shadow-sm"
            >
              <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 text-white flex items-center justify-center font-bold text-[11px] shadow-sm">
                {user.full_name.charAt(0)}
              </div>
              <span className="font-semibold text-white hidden sm:inline">{user.full_name}</span>
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <ChevronDown className="w-3 h-3 text-gray-400" />
            </motion.button>

            {/* Profile Popover Card */}
            <AnimatePresence>
              {isUserMenuOpen && (
                <motion.div
                  initial={{ opacity: 0, y: 8, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 8, scale: 0.95 }}
                  transition={{ duration: 0.15 }}
                  className="absolute right-0 mt-2 w-72 glass-panel rounded-2xl shadow-2xl p-4 z-50 border border-surface-border space-y-4 glow-primary"
                >
                  <div className="flex items-center gap-3 pb-3 border-b border-surface-border">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white flex items-center justify-center font-bold text-sm shadow-md">
                      {user.full_name.charAt(0)}
                    </div>
                    <div className="overflow-hidden">
                      <h4 className="text-xs font-bold text-white truncate">{user.full_name}</h4>
                      <p className="text-[11px] text-gray-400 truncate">{user.email}</p>
                      <span className="inline-block text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase mt-0.5">
                        STAFF ARCHITECT (ADMIN)
                      </span>
                    </div>
                  </div>

                  <div className="space-y-1 text-xs">
                    <button
                      onClick={() => {
                        if (onNavigate) onNavigate('settings');
                        setIsUserMenuOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 rounded-xl text-gray-300 hover:text-white hover:bg-surface-hover flex items-center gap-2 transition"
                    >
                      <Settings className="w-4 h-4 text-gray-400" />
                      <span>Workspace & Model Settings</span>
                    </button>
                    <button
                      onClick={() => {
                        onOpenCommandMenu();
                        setIsUserMenuOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 rounded-xl text-gray-300 hover:text-white hover:bg-surface-hover flex items-center gap-2 transition"
                    >
                      <Command className="w-4 h-4 text-gray-400" />
                      <span>Keyboard Shortcuts Cheat Sheet</span>
                    </button>
                  </div>

                  <div className="pt-2 border-t border-surface-border">
                    <button
                      onClick={() => {
                        setIsUserMenuOpen(false);
                        onLogout();
                      }}
                      className="w-full px-3 py-2 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/30 text-rose-300 text-xs font-semibold flex items-center justify-center gap-1.5 transition"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      <span>Sign Out of Workspace</span>
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </div>
    </header>
  );
};
