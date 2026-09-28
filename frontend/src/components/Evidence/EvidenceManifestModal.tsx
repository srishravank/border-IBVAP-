import React, { useState } from 'react';
import { EvidenceManifest } from '../../types';

interface EvidenceManifestModalProps {
  isOpen: boolean;
  onClose: () => void;
  manifest: EvidenceManifest | null;
  evidenceId: string;
}

export const EvidenceManifestModal: React.FC<EvidenceManifestModalProps> = ({
  isOpen,
  onClose,
  manifest,
  evidenceId,
}) => {
  const [copied, setCopied] = useState(false);

  if (!isOpen || !manifest) return null;

  const jsonString = JSON.stringify(manifest, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-forensic-surface border border-forensic-border rounded max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-forensic-border bg-forensic-elevated">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded bg-forensic-bg border border-forensic-border text-forensic-text">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xs font-bold text-forensic-text uppercase tracking-widest font-mono">Evidence Manifest</h3>
                <span className="text-xs px-2 py-0.5 rounded bg-forensic-bg text-forensic-text font-mono font-bold border border-forensic-border">
                  {evidenceId}
                </span>
                <span className="text-xs px-2 py-0.5 rounded bg-forensic-bg text-forensic-muted font-mono border border-forensic-border">
                  v{manifest.version}
                </span>
              </div>
              <p className="text-xs text-forensic-muted font-mono mt-0.5">
                Deterministic RFC 8785 canonical JSON schema • Source for SHA-256 hash
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className={`px-3 py-1.5 rounded text-xs font-mono font-bold flex items-center gap-1.5 transition border ${
                copied
                  ? 'bg-[#C7FF3D]/10 border-emerald-500/40 text-emerald-800 dark:text-[#C7FF3D]'
                  : 'bg-forensic-surface hover:bg-forensic-bg border-forensic-border text-forensic-text'
              }`}
            >
              {copied ? (
                <>
                  <svg className="w-3.5 h-3.5 text-emerald-600 dark:text-[#C7FF3D]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  Copied!
                </>
              ) : (
                <>
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Copy JSON
                </>
              )}
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded text-forensic-muted hover:text-forensic-text hover:bg-forensic-bg transition"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Breakdown bar */}
        <div className="bg-forensic-bg px-6 py-2.5 border-b border-forensic-border flex items-center gap-4 text-xs font-mono overflow-x-auto">
          <div className="flex items-center gap-1.5 text-forensic-text">
            <span className="w-2 h-2 rounded-full bg-forensic-text"></span>
            Events: <span className="font-bold">{manifest.events?.length || 0}</span>
          </div>
          <div className="flex items-center gap-1.5 text-forensic-text">
            <span className="w-2 h-2 rounded-full bg-neutral-500"></span>
            Cameras: <span className="font-bold">{manifest.journey?.cameras_visited_count || 1}</span>
          </div>
          <div className="flex items-center gap-1.5 text-forensic-text">
            <span className="w-2 h-2 rounded-full bg-[#F5A623]"></span>
            Risk Factors: <span className="text-[#F5A623] font-bold">{manifest.risk_assessment?.factors?.length || 0}</span>
          </div>
          <div className="flex items-center gap-1.5 text-forensic-text">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            Operator Actions: <span className="text-emerald-800 dark:text-[#C7FF3D] font-bold">{manifest.operator_actions?.length || 0}</span>
          </div>
          <div className="flex items-center gap-1.5 text-forensic-text">
            <span className="w-2 h-2 rounded-full bg-purple-500"></span>
            Media Refs: <span className="text-purple-700 dark:text-purple-400 font-bold">{manifest.media_references?.length || 0}</span>
          </div>
        </div>

        {/* Code View */}
        <div className="flex-1 p-4 overflow-y-auto bg-forensic-bg font-mono text-xs text-forensic-text leading-relaxed select-text">
          <pre className="whitespace-pre-wrap break-all">{jsonString}</pre>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-forensic-border bg-forensic-elevated flex items-center justify-between text-xs text-forensic-muted font-mono">
          <span>Schema: IBVAP-Evidence-v1.0 (PROVE Layer)</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded bg-forensic-surface hover:bg-forensic-bg text-forensic-text font-mono text-xs border border-forensic-border transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
