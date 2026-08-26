import React from 'react';
import { CheckCircle2, AlertCircle, HelpCircle, AlertOctagon } from 'lucide-react';

interface ConfidenceBadgeProps {
  level: 'high' | 'moderate' | 'low' | 'insufficient_evidence';
  score?: number;
  showExplanation?: boolean;
  reason?: string;
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({
  level,
  score,
  showExplanation = false,
  reason,
}) => {
  const configs = {
    high: {
      label: 'High Confidence',
      icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />,
      color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
      bar: 'bg-emerald-500',
    },
    moderate: {
      label: 'Moderate Confidence',
      icon: <AlertCircle className="w-3.5 h-3.5 text-amber-400" />,
      color: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
      bar: 'bg-amber-500',
    },
    low: {
      label: 'Low Confidence',
      icon: <HelpCircle className="w-3.5 h-3.5 text-rose-400" />,
      color: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
      bar: 'bg-rose-500',
    },
    insufficient_evidence: {
      label: 'Insufficient Evidence',
      icon: <AlertOctagon className="w-3.5 h-3.5 text-gray-400" />,
      color: 'bg-gray-500/10 text-gray-400 border-gray-500/30',
      bar: 'bg-gray-500',
    },
  };

  const current = configs[level] || configs.moderate;

  return (
    <div className="inline-flex flex-col gap-1">
      <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${current.color}`}>
        {current.icon}
        <span>{current.label}</span>
        {score !== undefined && (
          <span className="font-mono ml-1 opacity-75">({Math.round(score * 100)}%)</span>
        )}
      </div>
      {showExplanation && reason && (
        <p className="text-[11px] text-gray-400 max-w-sm leading-relaxed mt-0.5">
          {reason}
        </p>
      )}
    </div>
  );
};
