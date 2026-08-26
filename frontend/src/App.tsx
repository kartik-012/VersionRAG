import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar, ViewType } from './components/Sidebar';
import { CommandMenu } from './components/CommandMenu';
import { UploadModal } from './components/UploadModal';
import { ToastContainer, ToastMessage } from './components/Toast';
import { AuthView } from './views/AuthView';
import { DashboardView } from './views/DashboardView';
import { DocumentsView } from './views/DocumentsView';
import { VersionDetailView } from './views/VersionDetailView';
import { DiffView } from './views/DiffView';
import { TimelineView } from './views/TimelineView';
import { MigrationGuideView } from './views/MigrationGuideView';
import { SymbolHistoryView } from './views/SymbolHistoryView';
import { QueryStudioView } from './views/QueryStudioView';
import { EvaluationView } from './views/EvaluationView';
import { SettingsView } from './views/SettingsView';
import { User, Workspace, Project, Document, DocumentVersion, DocumentChange, EvaluationRun } from './types';
import { api } from './lib/api';

export function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);

  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [currentWorkspace, setCurrentWorkspace] = useState<Workspace | null>(null);

  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);

  const [documents, setDocuments] = useState<Document[]>([]);
  const [changes, setChanges] = useState<DocumentChange[]>([]);
  const [evaluations, setEvaluations] = useState<EvaluationRun[]>([]);

  const [currentView, setCurrentView] = useState<ViewType>('dashboard');
  const [selectedDocVersion, setSelectedDocVersion] = useState<{
    doc: Document;
    version: DocumentVersion;
  } | null>(null);

  const [isCommandMenuOpen, setIsCommandMenuOpen] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = (type: 'success' | 'error' | 'info', title: string, description?: string) => {
    const id = Date.now().toString();
    setToasts((prev) => [...prev, { id, type, title, description }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  // 1. Initial Authentication Check
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('versionrag_access_token');
      if (!token) {
        setAuthLoading(false);
        return;
      }
      try {
        const user = await api.getMe();
        setCurrentUser(user);
        await loadWorkspaces();
      } catch (err) {
        localStorage.removeItem('versionrag_access_token');
      } finally {
        setAuthLoading(false);
      }
    };
    checkAuth();
  }, []);

  // 2. Load Workspaces
  const loadWorkspaces = async () => {
    try {
      const wsList = await api.getWorkspaces();
      setWorkspaces(wsList);
      if (wsList.length > 0) {
        const defaultWs = wsList[0];
        setCurrentWorkspace(defaultWs);
        await loadProjects(defaultWs.id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // 3. Load Projects
  const loadProjects = async (workspaceId: string) => {
    try {
      const projList = await api.getProjects(workspaceId);
      setProjects(projList);
      if (projList.length > 0) {
        const defaultProj = projList[0];
        setCurrentProject(defaultProj);
        await loadProjectData(defaultProj.id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // 4. Load Project Data (Documents, Changes, Evaluations)
  const loadProjectData = async (projectId: string) => {
    try {
      const docs = await api.getDocuments(projectId);
      setDocuments(docs);
      if (docs.length > 0) {
        const tl = await api.getDocumentTimeline(docs[0].id);
        setChanges(tl);
      }
      const evals = await api.getEvaluations(projectId);
      setEvaluations(evals);
    } catch (e) {
      console.error(e);
    }
  };

  // Switch Workspace Handler
  const handleSelectWorkspace = async (ws: Workspace) => {
    setCurrentWorkspace(ws);
    await loadProjects(ws.id);
    showToast('info', 'Workspace Switched', `Active: ${ws.name}`);
  };

  // Switch Project Handler
  const handleSelectProject = async (proj: Project) => {
    setCurrentProject(proj);
    await loadProjectData(proj.id);
    showToast('info', 'Project Track Switched', `Active: ${proj.name}`);
  };

  // Logout Handler
  const handleLogout = () => {
    api.logout();
    setCurrentUser(null);
    showToast('info', 'Signed Out', 'Session terminated securely.');
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center text-xs text-gray-500 font-mono">
        Initializing VersionRAG 2.0 Ultra Platform...
      </div>
    );
  }

  if (!currentUser) {
    return (
      <AuthView
        onAuthenticated={(user) => {
          setCurrentUser(user);
          loadWorkspaces();
          showToast('success', `Welcome back, ${user.full_name}`, 'Signed in successfully.');
        }}
      />
    );
  }

  return (
    <div className="min-h-screen bg-background text-gray-100 flex flex-col antialiased">
      {/* Top Navigation */}
      <Navbar
        user={currentUser}
        currentWorkspace={currentWorkspace}
        workspaces={workspaces}
        onSelectWorkspace={handleSelectWorkspace}
        onNewWorkspace={async () => {
          const name = prompt('Enter new workspace name:');
          if (name) {
            await api.createWorkspace(name);
            await loadWorkspaces();
            showToast('success', 'Workspace Created', name);
          }
        }}
        currentProject={currentProject}
        projects={projects}
        onSelectProject={handleSelectProject}
        onNewProject={async () => {
          if (!currentWorkspace) return;
          const name = prompt('Enter new project track name:');
          if (name) {
            await api.createProject(currentWorkspace.id, name);
            await loadProjects(currentWorkspace.id);
            showToast('success', 'Project Track Created', name);
          }
        }}
        activeVersionTag={selectedDocVersion?.version.version_tag || null}
        onOpenCommandMenu={() => setIsCommandMenuOpen(true)}
        onOpenUploadModal={() => setIsUploadModalOpen(true)}
        onNavigate={(v) => {
          setSelectedDocVersion(null);
          setCurrentView(v);
        }}
        onLogout={handleLogout}
      />

      {/* Main Workspace Frame */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar
          currentView={currentView}
          onChangeView={(v) => {
            setSelectedDocVersion(null);
            setCurrentView(v);
          }}
          workspaces={workspaces}
          currentWorkspace={currentWorkspace}
          onSelectWorkspace={handleSelectWorkspace}
          onNewWorkspace={async () => {
            const name = prompt('Enter new workspace name:');
            if (name) {
              await api.createWorkspace(name);
              await loadWorkspaces();
              showToast('success', 'Workspace Created', name);
            }
          }}
          projects={projects}
          currentProject={currentProject}
          onSelectProject={handleSelectProject}
          onNewProject={async () => {
            if (!currentWorkspace) return;
            const name = prompt('Enter new project track name:');
            if (name) {
              await api.createProject(currentWorkspace.id, name);
              await loadProjects(currentWorkspace.id);
              showToast('success', 'Project Track Created', name);
            }
          }}
        />

        {/* Dynamic Center Stage Content */}
        <main className="flex-1 overflow-y-auto bg-background">
          {selectedDocVersion ? (
            <VersionDetailView
              document={selectedDocVersion.doc}
              version={selectedDocVersion.version}
              onBack={() => setSelectedDocVersion(null)}
              onCompareWithPrevious={() => {
                setSelectedDocVersion(null);
                setCurrentView('diff');
              }}
              onAskAIAboutVersion={(tag) => {
                setSelectedDocVersion(null);
                setCurrentView('query');
              }}
            />
          ) : currentView === 'dashboard' ? (
            <DashboardView
              project={currentProject}
              documents={documents}
              changes={changes}
              latestEvaluation={evaluations[0] || null}
              onChangeView={setCurrentView}
              onOpenUploadModal={() => setIsUploadModalOpen(true)}
            />
          ) : currentView === 'documents' ? (
            <DocumentsView
              documents={documents}
              onOpenUploadModal={() => setIsUploadModalOpen(true)}
              onSelectVersion={(doc, ver) => setSelectedDocVersion({ doc, version: ver })}
              onDeleteDocument={async (docId) => {
                if (confirm('Are you sure you want to delete this document family?')) {
                  await api.deleteDocument(docId);
                  if (currentProject) await loadProjectData(currentProject.id);
                  showToast('success', 'Document Family Removed');
                }
              }}
            />
          ) : currentView === 'diff' ? (
            <DiffView documents={documents} />
          ) : currentView === 'migration' ? (
            <MigrationGuideView documents={documents} />
          ) : currentView === 'symbols' ? (
            <SymbolHistoryView documents={documents} />
          ) : currentView === 'timeline' ? (
            <TimelineView documents={documents} changes={changes} />
          ) : currentView === 'query' ? (
            <QueryStudioView
              project={currentProject}
              activeVersionTag={documents[0]?.latest_version || null}
              onOpenDocumentReader={(vTag) => {
                const targetDoc = documents[0];
                const targetVer = targetDoc?.versions.find((v) => v.version_tag === vTag);
                if (targetDoc && targetVer) {
                  setSelectedDocVersion({ doc: targetDoc, version: targetVer });
                }
              }}
            />
          ) : currentView === 'evaluations' ? (
            <EvaluationView project={currentProject} />
          ) : (
            <SettingsView
              workspace={currentWorkspace}
              project={currentProject}
              currentUser={currentUser}
            />
          )}
        </main>
      </div>

      {/* Global Command Menu */}
      <CommandMenu
        isOpen={isCommandMenuOpen}
        onClose={() => setIsCommandMenuOpen(false)}
        onNavigate={(v) => {
          setSelectedDocVersion(null);
          setCurrentView(v);
        }}
      />

      {/* Global Document Upload Modal */}
      {currentProject && (
        <UploadModal
          isOpen={isUploadModalOpen}
          onClose={() => setIsUploadModalOpen(false)}
          projectId={currentProject.id}
          onUploadComplete={() => {
            if (currentProject) loadProjectData(currentProject.id);
            showToast('success', 'Pipeline Complete', 'New version indexed into knowledge base.');
          }}
        />
      )}

      {/* Toast Notification Container */}
      <ToastContainer
        toasts={toasts}
        onDismiss={(id) => setToasts((prev) => prev.filter((t) => t.id !== id))}
      />
    </div>
  );
}

export default App;
