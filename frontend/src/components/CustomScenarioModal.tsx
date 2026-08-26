import React, { useState } from 'react';
import { Play, Sparkles, X, PlusCircle, AlertCircle } from 'lucide-react';
import { api } from '../lib/api';

interface CustomScenarioModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  availableVersions: string[];
  onScenarioAdded: () => void;
}

export const CustomScenarioModal: React.FC<CustomScenarioModalProps> = ({
  isOpen,
  onClose,
  projectId,
  availableVersions,
  onScenarioAdded,
}) => {
  const [question, setQuestion] = useState('');
  const [targetVersion, setTargetVersion] = useState(availableVersions[0] || 'v15.14.0');
  const [groundTruth, setGroundTruth] = useState('');
  const [archetype, setArchetype] = useState('version_specific_query');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || !groundTruth.trim()) return;

    setLoading(true);
    setError(null);
    try {
      await api.addCustomScenario({
        project_id: projectId,
        question: question.trim(),
        target_version: targetVersion,
        ground_truth: groundTruth.trim(),
        archetype: archetype,
      });
      onScenarioAdded();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to add custom benchmark scenario');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-surface border border-surface-border w-full max-w-lg rounded-2xl shadow-2xl p-6 relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-white">
          <X className="w-5 h-5" />
        </button>

        <h3 className="text-base font-bold text-white mb-1 flex items-center gap-2">
          <PlusCircle className="w-5 h-5 text-emerald-400" />
          Design Custom Evaluation Benchmark Scenario
        </h3>
        <p className="text-xs text-gray-400 mb-5">
          Add an original test case to challenge Naive RAG vs VersionRAG in real-time.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block font-medium text-gray-300 mb-1">Query Archetype</label>
            <select
              value={archetype}
              onChange={(e) => setArchetype(e.target.value)}
              className="w-full bg-surface-subtle border border-surface-border rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary"
            >
              <option value="version_specific_query">Version-Specific Query</option>
              <option value="version_comparison_query">Version Comparison Query</option>
              <option value="change_query">Change / Evolution Query</option>
              <option value="conflict_query">Conflict / Discrepancy Query</option>
              <option value="silent_change_query">Silent / Undocumented Change Query</option>
              <option value="temporal_query">Temporal History Query</option>
            </select>
          </div>

          <div>
            <label className="block font-medium text-gray-300 mb-1">Target Version</label>
            <select
              value={targetVersion}
              onChange={(e) => setTargetVersion(e.target.value)}
              className="w-full bg-surface-subtle border border-surface-border rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary font-mono"
            >
              {availableVersions.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block font-medium text-gray-300 mb-1">Question / Prompt</label>
            <input
              type="text"
              required
              placeholder="e.g. Does assert.deepEqual() throw an error when comparing functions in this release?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              className="w-full bg-surface-subtle border border-surface-border rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-primary"
            />
          </div>

          <div>
            <label className="block font-medium text-gray-300 mb-1">Ground Truth Verified Answer</label>
            <textarea
              required
              rows={3}
              placeholder="e.g. Yes, functions are compared by reference only and throw AssertionError on mismatch."
              value={groundTruth}
              onChange={(e) => setGroundTruth(e.target.value)}
              className="w-full bg-surface-subtle border border-surface-border rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-primary font-mono"
            />
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-gray-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold flex items-center gap-1.5 transition shadow-sm shadow-emerald-600/30 disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{loading ? 'Evaluating Scenario...' : 'Add & Re-Score Benchmark'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
