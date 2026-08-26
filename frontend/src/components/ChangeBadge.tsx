import React from 'react';
import { Plus, Minus, Edit3, AlertTriangle, EyeOff, ShieldAlert, FileText } from 'lucide-react';
import { ChangeType, ChangeSeverity } from '../types';

interface ChangeBadgeProps {
  type: ChangeType;
  severity?: ChangeSeverity;
  isBreaking?: boolean;
  isSilent?: boolean;
}

export const ChangeBadge: React.FC<ChangeBadgeProps> = ({
  type,
  isBreaking = false,
  isSilent = false,
}) => {
  if (isBreaking) {
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded bg-fuchsia-500/15 text-fuchsia-400 border border-fuchsia-500/30">
        <ShieldAlert className="w-3 h-3 text-fuchsia-400" />
        Breaking
      </span>
    );
  }

  if (isSilent) {
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded bg-purple-500/15 text-purple-400 border border-purple-500/30">
        <EyeOff className="w-3 h-3 text-purple-400" />
        Silent Change
      </span>
    );
  }

  const config: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
    added: {
      label: 'Added',
      icon: <Plus className="w-3 h-3 text-emerald-400" />,
      color: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    },
    removed: {
      label: 'Removed',
      icon: <Minus className="w-3 h-3 text-rose-400" />,
      color: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
    },
    modified: {
      label: 'Modified',
      icon: <Edit3 className="w-3 h-3 text-sky-400" />,
      color: 'bg-sky-500/15 text-sky-400 border-sky-500/30',
    },
    deprecated: {
      label: 'Deprecated',
      icon: <AlertTriangle className="w-3 h-3 text-amber-400" />,
      color: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    },
    behavioral: {
      label: 'Behavioral',
      icon: <AlertTriangle className="w-3 h-3 text-indigo-400" />,
      color: 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30',
    },
    doc_only: {
      label: 'Docs Only',
      icon: <FileText className="w-3 h-3 text-gray-400" />,
      color: 'bg-gray-500/15 text-gray-400 border-gray-500/30',
    },
  };

  const item = config[type] || config.modified;

  return (
    <span className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded border ${item.color}`}>
      {item.icon}
      {item.label}
    </span>
  );
};
