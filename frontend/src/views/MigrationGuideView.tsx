import React, { useState, useEffect } from 'react';
import {
  GitPullRequest, ShieldAlert, Download, Sparkles,
  Code2, AlertTriangle, Copy, Check, Terminal,
  FileCode2, Zap, BookOpen, EyeOff, CheckCircle2
} from 'lucide-react';
import { Document } from '../types';
import { api } from '../lib/api';

interface MigrationGuideViewProps {
  documents: Document[];
}

const SAMPLE_PRESETS = [
  {
    label: 'Node.js v14 Production Suite (Silent + Breaking)',
    code: `const assert = require('assert');

// 1. Legacy CallTracker initialization
const tracker = new assert.CallTracker();
const callstub = tracker.calls(1);

// 2. Object comparison relying on v14 prototype / Symbol rules
function verifyPaymentPayload(actual, expected) {
  assert.deepEqual(actual, expected);
  assert.equal(actual.status, 200);
}

// 3. Verify tracker calls at teardown
process.on('exit', () => {
  tracker.verify();
});`,
  },
  {
    label: 'Silent Equality & Prototype Drift',
    code: `const assert = require('assert');

function checkSessionTokens(userToken, cachedToken) {
  // Relies on loose prototype & symbol property comparison in v14.0.0
  assert.deepEqual(userToken, cachedToken);
  return true;
}`,
  },
];

export const MigrationGuideView: React.FC<MigrationGuideViewProps> = ({ documents }) => {
  const [activeTab, setActiveTab] = useState<'scanner' | 'guide'>('scanner');
  const [selectedDocId, setSelectedDocId] = useState<string>(documents[0]?.id || '');
  const [fromVersionId, setFromVersionId] = useState<string>('');
  const [toVersionId, setToVersionId] = useState<string>('');

  // Code Scanner State
  const [codeSnippet, setCodeSnippet] = useState<string>(SAMPLE_PRESETS[0].code);
  const [scanResult, setScanResult] = useState<any | null>(null);
  const [scanning, setScanning] = useState(false);
  const [outputView, setOutputView] = useState<'side-by-side' | 'unified-diff'>('side-by-side');
  const [copiedRefactored, setCopiedRefactored] = useState(false);

  // Migration Guide State
  const [guideData, setGuideData] = useState<any | null>(null);
  const [loadingGuide, setLoadingGuide] = useState(false);
  const [copiedGuide, setCopiedGuide] = useState(false);

  const selectedDoc = documents.find((d) => d.id === selectedDocId);

  useEffect(() => {
    if (selectedDoc && selectedDoc.versions.length >= 2) {
      setFromVersionId(selectedDoc.versions[0].id);
      setToVersionId(selectedDoc.versions[selectedDoc.versions.length - 1].id);
    }
  }, [selectedDocId, documents]);

  const handleScanCode = async () => {
    if (!fromVersionId || !toVersionId || !codeSnippet.trim()) return;
    setScanning(true);
    try {
      const res = await api.scanProductionCode({
        from_version_id: fromVersionId,
        to_version_id: toVersionId,
        code_snippet: codeSnippet,
      });
      setScanResult(res);
    } catch (err: any) {
      alert(err.message || 'Failed to scan production code');
    } finally {
      setScanning(false);
    }
  };

  const handleGenerateGuide = async () => {
    if (!fromVersionId || !toVersionId) return;
    setLoadingGuide(true);
    try {
      const res = await api.getMigrationGuide(fromVersionId, toVersionId);
      setGuideData(res);
    } catch (err: any) {
      alert(err.message || 'Failed to generate migration guide');
    } finally {
      setLoadingGuide(false);
    }
  };

  const handleCopyRefactored = () => {
    if (scanResult?.refactored_code) {
      navigator.clipboard.writeText(scanResult.refactored_code);
      setCopiedRefactored(true);
      setTimeout(() => setCopiedRefactored(false), 2000);
    }
  };

  const handleCopyMarkdown = () => {
    if (guideData?.markdown_guide) {
      navigator.clipboard.writeText(guideData.markdown_guide);
      setCopiedGuide(true);
      setTimeout(() => setCopiedGuide(false), 2000);
    }
  };

  const handleDownloadMarkdown = () => {
    if (guideData?.markdown_guide) {
      const blob = new Blob([guideData.markdown_guide], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Migration_Guide_${guideData.from_tag}_to_${guideData.to_tag}.md`;
      a.click();
    }
  };

  const findingsByLine = React.useMemo(() => {
    const map = new Map<number, any>();
    if (scanResult?.line_findings) {
      for (const f of scanResult.line_findings) {
        map.set(f.line_number, f);
      }
    }
    return map;
  }, [scanResult]);

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header & Version Trajectory Bar */}
      <div className="bg-surface border border-surface-border rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                <GitPullRequest className="w-5 h-5 text-indigo-400" />
                Codebase Impact Scanner & Upgrade Synthesizer
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-mono font-bold uppercase rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                AST Diff Auditor
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-0.5">
              Audit production code against the indexed AST Diff Graph to pinpoint exact breaking lines, silent behavior shifts, and auto-refactored target code.
            </p>
          </div>

          {/* Mode Switcher Tabs */}
          <div className="flex items-center bg-surface-subtle p-1 rounded-xl border border-surface-border">
            <button
              onClick={() => setActiveTab('scanner')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                activeTab === 'scanner'
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>Live Codebase Scanner</span>
            </button>
            <button
              onClick={() => setActiveTab('guide')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                activeTab === 'guide'
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Migration Roadmap</span>
            </button>
          </div>
        </div>

        {/* Version Selectors */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-surface-border">
          <div>
            <label className="block text-[11px] font-medium text-gray-400 mb-1">Document Family</label>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="w-full bg-surface-subtle border border-surface-border text-xs rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary"
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.title}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-gray-400 mb-1">Current Production Version (From)</label>
            <select
              value={fromVersionId}
              onChange={(e) => setFromVersionId(e.target.value)}
              className="w-full bg-surface-subtle border border-surface-border text-xs rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary font-mono"
            >
              {selectedDoc?.versions.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.version_tag}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-gray-400 mb-1">Target Upgrade Version (To)</label>
            <select
              value={toVersionId}
              onChange={(e) => setToVersionId(e.target.value)}
              className="w-full bg-surface-subtle border border-surface-border text-xs rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary font-mono"
            >
              {selectedDoc?.versions.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.version_tag}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* ===================================================================== */}
      {/* TAB 1: LIVE CODEBASE IMPACT & BREAKING-CHANGE SCANNER                 */}
      {/* ===================================================================== */}
      {activeTab === 'scanner' && (
        <div className="space-y-6">
          {/* Code Input Workbench */}
          <div className="bg-surface border border-surface-border rounded-2xl p-5 shadow-lg space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <FileCode2 className="w-4 h-4 text-indigo-400" />
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  Paste Production Code Snippet
                </span>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <span className="text-[11px] text-gray-400">Presets:</span>
                {SAMPLE_PRESETS.map((preset, idx) => (
                  <button
                    key={idx}
                    onClick={() => setCodeSnippet(preset.code)}
                    className="px-2.5 py-1 rounded-md bg-surface-subtle hover:bg-surface-hover border border-surface-border text-[11px] text-gray-300 transition"
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
            </div>

            <textarea
              value={codeSnippet}
              onChange={(e) => setCodeSnippet(e.target.value)}
              rows={11}
              placeholder="Paste your Node.js, TypeScript, Python, or REST client code here..."
              className="w-full bg-background border border-surface-border rounded-xl p-4 font-mono text-xs text-gray-200 focus:outline-none focus:border-primary leading-relaxed resize-y"
            />

            <div className="flex items-center justify-between pt-1">
              <span className="text-[11px] text-gray-400">
                Scans every call site against AST signature diffs, parameter arity rules, and silent behavioral changes.
              </span>
              <button
                onClick={handleScanCode}
                disabled={scanning || !fromVersionId || !toVersionId || !codeSnippet.trim()}
                className="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold shadow-lg shadow-primary/30 flex items-center gap-2 transition disabled:opacity-50"
              >
                <Zap className="w-4 h-4" />
                <span>{scanning ? 'Auditing AST Graph...' : 'Scan Codebase & Auto-Refactor'}</span>
              </button>
            </div>
          </div>

          {/* Scan Results */}
          {scanResult && (
            <div className="space-y-6">
              {/* Risk Score & Metrics Banner */}
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                <div className="md:col-span-2 p-5 rounded-2xl bg-surface border border-surface-border flex items-center justify-between">
                  <div className="space-y-1">
                    <span className="text-[11px] text-gray-400 uppercase font-semibold">
                      Upgrade Compatibility Score
                    </span>
                    <div className="flex items-center gap-2.5">
                      <span className="text-3xl font-extrabold font-mono text-white">
                        {scanResult.compatibility_score}%
                      </span>
                      <span
                        className={`text-[11px] font-mono font-bold uppercase px-2.5 py-0.5 rounded-full ${
                          scanResult.risk_level === 'CRITICAL'
                            ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                            : scanResult.risk_level === 'HIGH'
                            ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                            : scanResult.risk_level === 'MODERATE'
                            ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30'
                            : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        }`}
                      >
                        {scanResult.risk_level} RISK
                      </span>
                    </div>
                    <p className="text-[11px] text-gray-400">
                      Trajectory: <span className="font-mono text-gray-200">{scanResult.from_tag}</span> →{' '}
                      <span className="font-mono text-emerald-400">{scanResult.to_tag}</span>
                    </p>
                  </div>
                  <div
                    className={`w-12 h-12 rounded-2xl flex items-center justify-center ${
                      scanResult.risk_level === 'SAFE'
                        ? 'bg-emerald-500/15 text-emerald-400'
                        : 'bg-rose-500/15 text-rose-400'
                    }`}
                  >
                    {scanResult.risk_level === 'SAFE' ? (
                      <CheckCircle2 className="w-6 h-6" />
                    ) : (
                      <ShieldAlert className="w-6 h-6" />
                    )}
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-surface border border-surface-border flex flex-col justify-center">
                  <span className="text-[11px] text-gray-400">Vulnerable Lines</span>
                  <span className="text-2xl font-bold font-mono text-rose-400 mt-1">
                    {scanResult.summary_counts.vulnerable_lines}{' '}
                    <span className="text-xs text-gray-500 font-normal">
                      / {scanResult.summary_counts.total_lines_scanned}
                    </span>
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-surface border border-surface-border flex flex-col justify-center">
                  <span className="text-[11px] text-gray-400 flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3 text-rose-400" /> Breaking Calls
                  </span>
                  <span className="text-2xl font-bold font-mono text-white mt-1">
                    {scanResult.summary_counts.breaking_lines}
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-surface border border-surface-border flex flex-col justify-center">
                  <span className="text-[11px] text-gray-400 flex items-center gap-1">
                    <EyeOff className="w-3 h-3 text-purple-400" /> Silent Shifts
                  </span>
                  <span className="text-2xl font-bold font-mono text-purple-400 mt-1">
                    {scanResult.summary_counts.silent_lines}
                  </span>
                </div>
              </div>

              {/* Code Comparison & Auto-Refactored Output */}
              <div className="bg-surface border border-surface-border rounded-2xl p-5 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <Code2 className="w-4 h-4 text-emerald-400" />
                    <h3 className="text-sm font-bold text-white">
                      Line-Highlighted Vulnerability Map & Auto-Refactored Code ({scanResult.to_tag})
                    </h3>
                  </div>

                  <div className="flex items-center gap-2">
                    <div className="flex items-center bg-surface-subtle p-0.5 rounded-lg border border-surface-border text-[11px]">
                      <button
                        onClick={() => setOutputView('side-by-side')}
                        className={`px-2.5 py-1 rounded-md font-medium transition ${
                          outputView === 'side-by-side'
                            ? 'bg-primary text-white'
                            : 'text-gray-400 hover:text-white'
                        }`}
                      >
                        Side-by-Side
                      </button>
                      <button
                        onClick={() => setOutputView('unified-diff')}
                        className={`px-2.5 py-1 rounded-md font-medium transition ${
                          outputView === 'unified-diff'
                            ? 'bg-primary text-white'
                            : 'text-gray-400 hover:text-white'
                        }`}
                      >
                        Unified Diff
                      </button>
                    </div>

                    <button
                      onClick={handleCopyRefactored}
                      className="px-3 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/30 text-emerald-300 text-xs font-semibold flex items-center gap-1.5 transition"
                    >
                      {copiedRefactored ? (
                        <Check className="w-3.5 h-3.5" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                      <span>{copiedRefactored ? 'Copied Upgrade' : `Copy ${scanResult.to_tag} Code`}</span>
                    </button>
                  </div>
                </div>

                {outputView === 'side-by-side' ? (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 font-mono text-xs">
                    {/* Left: Annotated Original Code */}
                    <div className="rounded-xl bg-background border border-surface-border overflow-hidden">
                      <div className="px-3.5 py-2 bg-surface-subtle border-b border-surface-border text-[11px] font-bold text-rose-400 flex items-center justify-between">
                        <span>Current Code ({scanResult.from_tag})</span>
                        <span>{scanResult.summary_counts.vulnerable_lines} Vulnerable Line(s)</span>
                      </div>
                      <div className="p-3 space-y-0.5 overflow-x-auto">
                        {scanResult.original_code.split('\n').map((lineText: string, i: number) => {
                          const lineNum = i + 1;
                          const finding = findingsByLine.get(lineNum);
                          return (
                            <div
                              key={lineNum}
                              className={`flex items-start gap-2.5 px-2 py-0.5 rounded ${
                                finding
                                  ? finding.is_silent
                                    ? 'bg-purple-500/15 border-l-2 border-purple-400 text-purple-200'
                                    : 'bg-rose-500/15 border-l-2 border-rose-500 text-rose-200'
                                  : 'text-gray-300'
                              }`}
                            >
                              <span className="w-6 text-right text-[10px] text-gray-500 select-none pt-0.5">
                                {lineNum}
                              </span>
                              <pre className="whitespace-pre-wrap break-all flex-1 leading-relaxed">
                                {lineText || ' '}
                              </pre>
                              {finding && (
                                <span
                                  className={`text-[9px] uppercase font-bold px-1.5 py-0.2 rounded shrink-0 ${
                                    finding.is_silent
                                      ? 'bg-purple-500/30 text-purple-300'
                                      : 'bg-rose-500/30 text-rose-300'
                                  }`}
                                >
                                  {finding.is_silent ? 'SILENT BREAK' : finding.change_type}
                                </span>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Right: Auto-Refactored Code */}
                    <div className="rounded-xl bg-background border border-emerald-500/30 overflow-hidden">
                      <div className="px-3.5 py-2 bg-emerald-500/10 border-b border-emerald-500/20 text-[11px] font-bold text-emerald-400 flex items-center justify-between">
                        <span>Auto-Refactored Code ({scanResult.to_tag})</span>
                        <span>Ready for Production</span>
                      </div>
                      <div className="p-3 space-y-0.5 overflow-x-auto">
                        {scanResult.refactored_code.split('\n').map((lineText: string, i: number) => {
                          const isChanged =
                            lineText.includes(`[${scanResult.to_tag}`) ||
                            lineText.includes('[REMOVED IN');
                          return (
                            <div
                              key={i}
                              className={`flex items-start gap-2.5 px-2 py-0.5 rounded ${
                                isChanged
                                  ? 'bg-emerald-500/15 border-l-2 border-emerald-400 text-emerald-200'
                                  : 'text-gray-300'
                              }`}
                            >
                              <span className="w-6 text-right text-[10px] text-gray-500 select-none pt-0.5">
                                {i + 1}
                              </span>
                              <pre className="whitespace-pre-wrap break-all flex-1 leading-relaxed">
                                {lineText || ' '}
                              </pre>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-xl bg-background border border-surface-border p-4 font-mono text-xs overflow-x-auto">
                    <pre className="leading-relaxed">
                      {(scanResult.unified_diff || 'No changes required.').split('\n').map((dLine: string, idx: number) => (
                        <div
                          key={idx}
                          className={
                            dLine.startsWith('+') && !dLine.startsWith('+++')
                              ? 'text-emerald-400 bg-emerald-500/10 px-2'
                              : dLine.startsWith('-') && !dLine.startsWith('---')
                              ? 'text-rose-400 bg-rose-500/10 px-2'
                              : dLine.startsWith('@@')
                              ? 'text-indigo-400 font-bold py-1'
                              : 'text-gray-400 px-2'
                          }
                        >
                          {dLine}
                        </div>
                      ))}
                    </pre>
                  </div>
                )}
              </div>

              {/* Detailed Line-by-Line Findings with Doc Citations */}
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-indigo-400" />
                  Line-by-Line AST Vulnerability Diagnostics & Verified Doc Citations ({scanResult.line_findings.length})
                </h3>

                {scanResult.line_findings.map((f: any, idx: number) => (
                  <div
                    key={idx}
                    className="bg-surface border border-surface-border rounded-2xl p-5 space-y-3 shadow-sm"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2.5">
                        <span className="px-2.5 py-1 rounded-lg bg-rose-500/20 border border-rose-500/30 text-rose-300 font-mono font-bold text-xs">
                          Line {f.line_number}
                        </span>
                        <span className="font-mono text-sm font-bold text-white">{f.symbol}</span>
                        {f.is_silent && (
                          <span className="px-2 py-0.5 rounded-full bg-purple-500/20 border border-purple-500/40 text-purple-300 text-[10px] font-mono font-bold uppercase flex items-center gap-1">
                            <EyeOff className="w-3 h-3" /> Undocumented Silent Break
                          </span>
                        )}
                      </div>

                      <span
                        className={`text-[10px] font-mono font-bold uppercase px-2.5 py-0.5 rounded ${
                          f.severity === 'CRITICAL'
                            ? 'bg-rose-500/20 text-rose-400'
                            : f.severity === 'HIGH'
                            ? 'bg-amber-500/20 text-amber-400'
                            : 'bg-indigo-500/20 text-indigo-300'
                        }`}
                      >
                        {f.severity} • {f.change_type}
                      </span>
                    </div>

                    <p className="text-xs text-gray-200 leading-relaxed">
                      <span className="font-semibold text-rose-300">Why it breaks: </span>
                      {f.issue_summary}
                    </p>

                    <p className="text-xs text-emerald-300 leading-relaxed">
                      <span className="font-semibold">Auto-Refactor Applied: </span>
                      {f.fix_explanation}
                    </p>

                    {/* Citation Box */}
                    <div className="p-3 rounded-xl bg-surface-subtle border border-surface-border text-[11px] space-y-1">
                      <div className="flex items-center justify-between text-gray-400">
                        <span className="font-semibold text-indigo-300">
                          Verified Citation • {f.citation.section}
                        </span>
                        <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300">
                          {f.citation.version_tag}
                        </span>
                      </div>
                      <p className="text-gray-400 font-mono text-[11px] line-clamp-2">
                        {f.citation.excerpt}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* TAB 2: AUTOMATED MIGRATION ROADMAP SYNTHESIZER                        */}
      {/* ===================================================================== */}
      {activeTab === 'guide' && (
        <div className="space-y-6">
          <div className="flex justify-end">
            <button
              onClick={handleGenerateGuide}
              disabled={loadingGuide || !fromVersionId || !toVersionId}
              className="px-5 py-2 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-semibold shadow-md shadow-primary/30 flex items-center gap-2 transition disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              <span>{loadingGuide ? 'Synthesizing Roadmap...' : 'Generate Migration Guide'}</span>
            </button>
          </div>

          {guideData ? (
            <div className="space-y-6">
              <div className="p-5 rounded-2xl bg-surface border border-surface-border shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm ${
                      guideData.risk_score === 'CRITICAL'
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        : guideData.risk_score === 'HIGH'
                        ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    }`}
                  >
                    <ShieldAlert className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-white">Migration Risk Assessment:</span>
                      <span
                        className={`text-xs font-mono font-bold uppercase px-2 py-0.5 rounded ${
                          guideData.risk_score === 'CRITICAL'
                            ? 'bg-rose-500/20 text-rose-400'
                            : guideData.risk_score === 'HIGH'
                            ? 'bg-amber-500/20 text-amber-400'
                            : 'bg-emerald-500/20 text-emerald-400'
                        }`}
                      >
                        {guideData.risk_score} RISK
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mt-0.5">
                      Trajectory: <span className="font-mono text-gray-200">{guideData.from_tag}</span> →{' '}
                      <span className="font-mono text-gray-200">{guideData.to_tag}</span> (
                      {guideData.breaking_count} breaking changes, {guideData.deprecated_count} deprecations)
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCopyMarkdown}
                    className="px-3 py-1.5 rounded-lg bg-surface-subtle hover:bg-surface-hover border border-surface-border text-gray-200 text-xs font-medium flex items-center gap-1.5 transition"
                  >
                    {copiedGuide ? (
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                    <span>{copiedGuide ? 'Copied' : 'Copy Guide'}</span>
                  </button>
                  <button
                    onClick={handleDownloadMarkdown}
                    className="px-3 py-1.5 rounded-lg bg-surface-subtle hover:bg-surface-hover border border-surface-border text-gray-200 text-xs font-medium flex items-center gap-1.5 transition"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download .MD</span>
                  </button>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Code2 className="w-4 h-4 text-primary" />
                  Automated Code Transformation Steps ({guideData.steps.length})
                </h3>

                {guideData.steps.map((st: any) => (
                  <div
                    key={st.step}
                    className="bg-surface border border-surface-border rounded-2xl p-5 shadow-sm space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <span className="w-6 h-6 rounded-full bg-primary/20 text-primary-light flex items-center justify-center font-mono font-bold text-xs">
                          {st.step}
                        </span>
                        <h4 className="text-sm font-semibold text-white">{st.title}</h4>
                      </div>
                      <span
                        className={`text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded ${
                          st.severity === 'CRITICAL'
                            ? 'bg-rose-500/20 text-rose-400'
                            : st.severity === 'HIGH'
                            ? 'bg-amber-500/20 text-amber-400'
                            : 'bg-emerald-500/20 text-emerald-400'
                        }`}
                      >
                        {st.severity}
                      </span>
                    </div>

                    <p className="text-xs text-gray-300">{st.description}</p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 text-xs font-mono">
                      <div className="p-3 rounded-xl bg-background border border-rose-500/20 text-rose-300">
                        <div className="text-[10px] uppercase font-bold text-rose-400 mb-1.5 flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                          Legacy Code ({guideData.from_tag})
                        </div>
                        <pre className="text-[11px] whitespace-pre-wrap leading-relaxed">{st.code_before}</pre>
                      </div>

                      <div className="p-3 rounded-xl bg-background border border-emerald-500/20 text-emerald-300">
                        <div className="text-[10px] uppercase font-bold text-emerald-400 mb-1.5 flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                          Refactored Code ({guideData.to_tag})
                        </div>
                        <pre className="text-[11px] whitespace-pre-wrap leading-relaxed">{st.code_after}</pre>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-16 bg-surface border border-surface-border rounded-2xl p-8">
              <GitPullRequest className="w-10 h-10 text-indigo-400 mx-auto mb-3 opacity-60" />
              <h3 className="text-sm font-semibold text-white">No migration guide synthesized yet</h3>
              <p className="text-xs text-gray-400 mt-1 max-w-md mx-auto">
                Click 'Generate Migration Guide' above to produce a step-by-step markdown upgrade roadmap.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
