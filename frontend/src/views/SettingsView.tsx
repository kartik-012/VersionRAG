import React, { useState, useEffect } from 'react';
import { Settings, Shield, UserPlus, Trash2, Check, ShieldCheck } from 'lucide-react';
import { Workspace, Project, User } from '../types';
import { api } from '../lib/api';

interface SettingsViewProps {
  workspace: Workspace | null;
  project: Project | null;
  currentUser: User | null;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  workspace,
  project,
  currentUser,
}) => {
  const [members, setMembers] = useState<any[]>([]);
  const [newEmail, setNewEmail] = useState('');
  const [newRole, setNewRole] = useState('member');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (workspace) {
      loadMembers();
    }
  }, [workspace]);

  const loadMembers = async () => {
    if (!workspace) return;
    try {
      const data = await api.getWorkspaceMembers(workspace.id);
      setMembers(data);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <Settings className="w-5 h-5 text-gray-400" />
          Workspace & RBAC Security Settings
        </h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Role-Based Access Control and Tenant Isolation Settings.
        </p>
      </div>

      {/* Workspace Info Card */}
      <div className="bg-surface border border-surface-border rounded-xl p-5 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-white">Active Workspace Information</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-3 bg-surface-subtle border border-surface-border rounded-lg">
            <span className="text-gray-500 block">Workspace Name</span>
            <span className="text-white font-medium text-sm mt-0.5 block">{workspace?.name}</span>
          </div>
          <div className="p-3 bg-surface-subtle border border-surface-border rounded-lg">
            <span className="text-gray-500 block">Tenant Slug</span>
            <span className="font-mono text-primary-light mt-0.5 block">{workspace?.slug}</span>
          </div>
        </div>
      </div>

      {/* RBAC Role Permissions Matrix */}
      <div className="bg-surface border border-surface-border rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Shield className="w-4 h-4 text-primary" />
            RBAC Membership & Permissions
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-surface-subtle text-gray-400 uppercase text-[10px] font-mono border-y border-surface-border">
              <tr>
                <th className="p-3">Member Email</th>
                <th className="p-3">Assigned Role</th>
                <th className="p-3">Tenant Boundary</th>
                <th className="p-3">Permissions Scope</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border text-gray-300">
              <tr className="hover:bg-surface-subtle/50 transition">
                <td className="p-3 font-medium text-white flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-primary/20 text-primary-light flex items-center justify-center font-bold text-xs">
                    {currentUser?.full_name.charAt(0)}
                  </div>
                  <span>{currentUser?.email} (You)</span>
                </td>
                <td className="p-3">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-blue-500/15 text-blue-400 border border-blue-500/30">
                    Owner
                  </span>
                </td>
                <td className="p-3 font-mono text-gray-400">Strictly Isolated</td>
                <td className="p-3 text-emerald-400 font-medium">Full Administrative Control</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
