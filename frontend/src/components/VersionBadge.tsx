import React from 'react';

interface VersionBadgeProps {
  version: string;
  size?: 'sm' | 'md' | 'lg';
  active?: boolean;
}

// Deterministic color assignment based on version tag string hash
const PALETTE = [
  'bg-blue-500/15 text-blue-400 border-blue-500/30',
  'bg-purple-500/15 text-purple-400 border-purple-500/30',
  'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  'bg-amber-500/15 text-amber-400 border-amber-500/30',
  'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
  'bg-rose-500/15 text-rose-400 border-rose-500/30',
];

export const VersionBadge: React.FC<VersionBadgeProps> = ({ version, size = 'md', active = false }) => {
  let hash = 0;
  for (let i = 0; i < version.length; i++) {
    hash = version.charCodeAt(i) + ((hash << 5) - hash);
  }
  const colorClass = PALETTE[Math.abs(hash) % PALETTE.length];

  const sizeClasses = {
    sm: 'text-[10px] px-1.5 py-0.5 rounded',
    md: 'text-xs px-2.5 py-1 rounded-md font-medium',
    lg: 'text-sm px-3 py-1.5 rounded-lg font-semibold',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono border ${colorClass} ${sizeClasses[size]} ${
        active ? 'ring-2 ring-primary ring-offset-1 ring-offset-background' : ''
      }`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80" />
      {version}
    </span>
  );
};
