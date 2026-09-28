import React, { useState, useEffect } from 'react';
import {
  EvidencePackage,
  EvidenceManifest,
  EvidenceVerificationResult,
  EvidenceAuditLogEntry,
  TamperDemoResult
} from '../../types';
import { api } from '../../services/api';
import { EvidenceManifestModal } from './EvidenceManifestModal';
import { Lock, ShieldCheck, AlertTriangle, CheckCircle2, RotateCcw, Copy, ExternalLink, Activity } from 'lucide-react';

interface EvidenceTrustPanelProps {
  incidentId: string;
  operatorId?: string;
  role?: string;
}

export const EvidenceTrustPanel: React.FC<EvidenceTrustPanelProps> = ({
  incidentId,
  operatorId = 'OP-9402',
  role = 'SUPERVISOR',
}) => {
  const [packages, setPackages] = useState<EvidencePackage[]>([]);
  const [activePackage, setActivePackage] = useState<EvidencePackage | null>(null);
  const [manifest, setManifest] = useState<EvidenceManifest | null>(null);
  const [verification, setVerification] = useState<EvidenceVerificationResult | null>(null);
  const [auditLogs, setAuditLogs] = useState<EvidenceAuditLogEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [tamperInfo, setTamperInfo] = useState<TamperDemoResult | null>(null);
  const [isManifestOpen, setIsManifestOpen] = useState<boolean>(false);
  const [copiedHash, setCopiedHash] = useState<boolean>(false);
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

  const fetchEvidenceData = async () => {
    try {
      setLoading(true);
      const pkgs = await api.getIncidentEvidencePackages(incidentId);
      setPackages(pkgs);
      if (pkgs.length > 0) {
        const pkg = pkgs[0];
        setActivePackage(pkg);
        if (pkg.latest_verification) {
          setVerification(pkg.latest_verification);
        }
        const logs = await api.getEvidenceAuditTrail(pkg.evidence_id);
        setAuditLogs(logs);
      } else {
        setActivePackage(null);
        setVerification(null);
        setAuditLogs([]);
      }
    } catch (err: any) {
      console.error('Failed to load evidence packages', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvidenceData();
  }, [incidentId]);

  const handleGeneratePackage = async () => {
    try {
      setActionLoading('generate');
      setFeedbackMsg({ type: 'info', text: 'Compiling evidence, computing RFC 8785 canonical hash & anchoring to blockchain ledger...' });
      const newPkg = await api.generateEvidencePackage(incidentId, {
        operator_id: operatorId,
        role: role,
        version: '1.0',
        notes: `Operational evidence package anchored by ${operatorId}`
      });
      setActivePackage(newPkg);
      await fetchEvidenceData();
      setFeedbackMsg({ type: 'success', text: `Evidence package ${newPkg.evidence_id} successfully compiled and anchored into Block #${newPkg.anchor?.block_number}!` });
      setTimeout(() => setFeedbackMsg(null), 5000);
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Failed to generate evidence package' });
    } finally {
      setActionLoading(null);
    }
  };

  const handleVerifyIntegrity = async () => {
    if (!activePackage) return;
    try {
      setActionLoading('verify');
      const res = await api.verifyEvidenceIntegrity(activePackage.evidence_id, {
        operator_id: operatorId,
        role: role
      });
      setVerification(res);
      const updatedLogs = await api.getEvidenceAuditTrail(activePackage.evidence_id);
      setAuditLogs(updatedLogs);

      if (res.is_authentic) {
        setFeedbackMsg({ type: 'success', text: 'Cryptographic match confirmed! SHA-256 hash matches immutable blockchain anchor.' });
      } else {
        setFeedbackMsg({ type: 'error', text: 'CRITICAL WARNING: Tampering detected! Local file hash does NOT match blockchain ledger anchor!' });
      }
      setTimeout(() => setFeedbackMsg(null), 6000);
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Integrity verification failed' });
    } finally {
      setActionLoading(null);
    }
  };

  const handleViewManifest = async () => {
    if (!activePackage) return;
    try {
      setActionLoading('manifest');
      const m = await api.getEvidenceManifest(activePackage.evidence_id);
      setManifest(m);
      setIsManifestOpen(true);
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: 'Failed to load manifest JSON' });
    } finally {
      setActionLoading(null);
    }
  };

  const handleTamperDemo = async () => {
    if (!activePackage) return;
    try {
      setActionLoading('tamper');
      const res = await api.tamperEvidenceDemo(activePackage.evidence_id);
      setTamperInfo(res);
      const verifRes = await api.verifyEvidenceIntegrity(activePackage.evidence_id, {
        operator_id: operatorId,
        role: role
      });
      setVerification(verifRes);
      const updatedLogs = await api.getEvidenceAuditTrail(activePackage.evidence_id);
      setAuditLogs(updatedLogs);
      setFeedbackMsg({
        type: 'error',
        text: `TAMPER SIMULATION APPLIED: ${res.field_modified} was altered on disk. Ledger integrity check flagged state as TAMPERED!`
      });
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Tamper simulation failed' });
    } finally {
      setActionLoading(null);
    }
  };

  const handleRestoreDemo = async () => {
    if (!activePackage) return;
    try {
      setActionLoading('restore');
      await api.restoreEvidenceDemo(activePackage.evidence_id);
      setTamperInfo(null);
      const verifRes = await api.verifyEvidenceIntegrity(activePackage.evidence_id, {
        operator_id: operatorId,
        role: role
      });
      setVerification(verifRes);
      const updatedLogs = await api.getEvidenceAuditTrail(activePackage.evidence_id);
      setAuditLogs(updatedLogs);
      setFeedbackMsg({
        type: 'success',
        text: 'ORIGINAL RESTORED: Evidence manifest restored from clean state. Ledger verification is now AUTHENTIC!'
      });
      setTimeout(() => setFeedbackMsg(null), 5000);
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Restore failed' });
    } finally {
      setActionLoading(null);
    }
  };

  const copyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-10 text-[#5E5E5E] font-mono text-xs">
        <Activity className="animate-spin mr-2 h-4 w-4 text-[#171717]" />
        Loading cryptographic evidence records...
      </div>
    );
  }

  if (!activePackage) {
    return (
      <div className="p-4 bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm space-y-4 font-mono text-xs">
        <div className="flex items-center gap-3">
          <Lock className="w-5 h-5 text-[#171717]" />
          <div>
            <h3 className="font-bold text-xs text-[#171717] uppercase">Evidence Trust & Blockchain Anchoring</h3>
            <p className="text-[10px] text-[#5E5E5E]">
              PROVE Layer: Compile deterministic, court-admissible evidence packages and anchor SHA-256 hashes to the ledger.
            </p>
          </div>
        </div>

        {feedbackMsg && (
          <div className="p-2.5 rounded-sm bg-[#F4F1E8] border border-[#D6D2C8] text-[10px] text-[#171717]">
            {feedbackMsg.text}
          </div>
        )}

        <div className="p-3 bg-[#F4F1E8] rounded-sm border border-[#D6D2C8] space-y-2 text-[10px] text-[#5E5E5E]">
          <span className="font-bold text-[#171717] uppercase block">Included Evidence Artifacts:</span>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            <div>● Incident Metadata</div>
            <div>● Verified Events</div>
            <div>● Multi-Camera Journey</div>
            <div>● Explainable Risk Scoring</div>
            <div>● Operator Decisions</div>
            <div>● Off-Chain Media Refs</div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            onClick={handleGeneratePackage}
            disabled={actionLoading === 'generate'}
            className="px-3 py-1.5 rounded-sm bg-[#171717] hover:bg-[#292929] text-[#F4F1E8] font-bold text-xs flex items-center gap-1.5 transition"
          >
            <Lock className="w-3.5 h-3.5 text-[#C7FF3D]" />
            <span>{actionLoading === 'generate' ? 'ANCHORING...' : 'GENERATE & ANCHOR EVIDENCE'}</span>
          </button>
        </div>
      </div>
    );
  }

  const isTampered = verification?.status === 'TAMPERED';

  return (
    <div className="space-y-4 font-sans font-mono text-xs">
      {/* Evidence Package Header */}
      <div className="p-3.5 bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-sm ${isTampered ? 'bg-[#FF4D4D] text-[#FFFFFF]' : 'bg-[#171717] text-[#C7FF3D]'}`}>
            <Lock className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-bold text-sm text-[#171717]">{activePackage.evidence_id}</span>
              <span className="text-[10px] px-1.5 py-0.2 bg-[#ECE9E0] text-[#171717] border border-[#D6D2C8] rounded-sm font-bold">
                v{activePackage.version}
              </span>
              <span className={`text-[10px] px-2 py-0.2 rounded-sm font-bold uppercase ${
                isTampered ? 'bg-[#FF4D4D] text-[#FFFFFF]' : 'bg-[#171717] text-[#C7FF3D]'
              }`}>
                ● {verification ? verification.status : activePackage.status}
              </span>
            </div>
            <p className="text-[10px] text-[#5E5E5E] mt-0.5">
              CREATED: {new Date(activePackage.created_at).toLocaleString()} • OPERATOR: {activePackage.created_by} ({activePackage.role})
            </p>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            onClick={handleViewManifest}
            disabled={actionLoading === 'manifest'}
            className="px-2.5 py-1 rounded-sm bg-[#FFFFFF] hover:bg-[#F4F1E8] text-[#171717] border border-[#D6D2C8] text-xs font-semibold flex items-center gap-1 transition"
          >
            <ExternalLink className="w-3 h-3" />
            <span>VIEW MANIFEST</span>
          </button>

          <button
            onClick={handleVerifyIntegrity}
            disabled={actionLoading === 'verify'}
            className="px-2.5 py-1 rounded-sm bg-[#171717] hover:bg-[#292929] text-[#F4F1E8] text-xs font-bold flex items-center gap-1 transition"
          >
            <CheckCircle2 className="w-3 h-3 text-[#C7FF3D]" />
            <span>{actionLoading === 'verify' ? 'VERIFYING...' : 'VERIFY INTEGRITY'}</span>
          </button>
        </div>
      </div>

      {feedbackMsg && (
        <div className={`p-2.5 rounded-sm border text-xs flex items-start gap-2 ${
          feedbackMsg.type === 'success'
            ? 'bg-[#F4F1E8] border-[#171717] text-[#171717]'
            : feedbackMsg.type === 'error'
            ? 'bg-[#FF4D4D] border-[#FF4D4D] text-[#FFFFFF]'
            : 'bg-[#F4F1E8] border-[#D6D2C8] text-[#171717]'
        }`}>
          <span>{feedbackMsg.type === 'success' ? '🛡️' : feedbackMsg.type === 'error' ? '⚠️' : 'ℹ️'}</span>
          <div className="flex-1">{feedbackMsg.text}</div>
        </div>
      )}

      {/* Grid: SHA-256 Hash Card + Blockchain Ledger Anchor Card */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {/* SHA-256 Card */}
        <div className="p-3 bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-bold text-xs text-[#171717] uppercase">
              CRYPTOGRAPHIC EVIDENCE HASH
            </span>
            <span className="text-[9px] px-1.5 py-0.2 rounded-sm bg-[#ECE9E0] text-[#5E5E5E] border border-[#D6D2C8]">
              RFC 8785 CANONICAL
            </span>
          </div>

          <div className="p-2.5 bg-[#F4F1E8] rounded-sm border border-[#D6D2C8] space-y-1">
            <div className="flex items-center justify-between text-[9px] text-[#5E5E5E]">
              <span>ALGORITHM: SHA-256</span>
              <span>SIZE: {activePackage.hash?.canonical_size_bytes || 0} bytes</span>
            </div>
            <div className="text-[11px] text-[#171717] break-all select-all font-bold">
              {activePackage.hash?.hash_value || 'N/A'}
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={() => copyHash(activePackage.hash?.hash_value || '')}
              className="text-[10px] text-[#5E5E5E] hover:text-[#171717] flex items-center gap-1 transition"
            >
              <Copy className="w-3 h-3" />
              <span>{copiedHash ? 'COPIED HASH' : 'COPY SHA-256 HASH'}</span>
            </button>
          </div>
        </div>

        {/* Blockchain Ledger Anchor Card */}
        <div className="p-3 bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-bold text-xs text-[#171717] uppercase">
              BLOCKCHAIN LEDGER ANCHOR
            </span>
            <span className="text-[9px] px-1.5 py-0.2 rounded-sm bg-[#171717] text-[#C7FF3D]">
              IMMUTABLE
            </span>
          </div>

          {activePackage.anchor ? (
            <div className="p-2.5 bg-[#F4F1E8] rounded-sm border border-[#D6D2C8] space-y-1 text-[10px]">
              <div className="flex justify-between items-center text-[#5E5E5E]">
                <span>TX ID:</span>
                <span className="text-[#171717] font-bold">{activePackage.anchor.transaction_id}</span>
              </div>
              <div className="flex justify-between items-center text-[#5E5E5E]">
                <span>BLOCK NUMBER:</span>
                <span className="text-[#171717] font-bold">#{activePackage.anchor.block_number}</span>
              </div>
              <div className="flex justify-between items-center text-[#5E5E5E]">
                <span>STATUS:</span>
                <span className="text-[#1A5319] font-bold">● {activePackage.anchor.status}</span>
              </div>
            </div>
          ) : (
            <div className="p-2.5 bg-[#F4F1E8] rounded-sm border border-[#D6D2C8] text-center text-[#5E5E5E]">
              No anchor found
            </div>
          )}

          <div className="text-[9px] text-[#8A877E]">
            Zero raw video on-chain • Digest anchored at {activePackage.anchor ? new Date(activePackage.anchor.timestamp).toLocaleTimeString() : ''}
          </div>
        </div>
      </div>

      {/* Interactive Tamper Demonstration Box */}
      <div className="p-3.5 bg-[#F4F1E8] border border-[#D6D2C8] rounded-sm space-y-2.5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h4 className="text-xs font-bold text-[#171717] uppercase">
              INTERACTIVE TAMPER DEMONSTRATION & VERIFICATION
            </h4>
            <p className="text-[10px] text-[#5E5E5E]">
              Simulate an adversary modifying off-chain files to demonstrate instant cryptographic detection.
            </p>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={handleTamperDemo}
              disabled={actionLoading === 'tamper'}
              className="px-2.5 py-1 rounded-sm bg-[#F5A623] hover:bg-[#d98216] text-[#171717] font-bold text-[10px] transition"
            >
              {actionLoading === 'tamper' ? 'TAMPERING...' : '⚠️ SIMULATE TAMPERING'}
            </button>
            <button
              onClick={handleRestoreDemo}
              disabled={actionLoading === 'restore'}
              className="px-2.5 py-1 rounded-sm bg-[#171717] hover:bg-[#292929] text-[#C7FF3D] font-bold text-[10px] transition"
            >
              {actionLoading === 'restore' ? 'RESTORING...' : '🔄 RESTORE ORIGINAL'}
            </button>
          </div>
        </div>

        {verification && (
          <div className={`p-3 rounded-sm border text-[10px] space-y-1.5 ${
            verification.is_authentic
              ? 'bg-[#FFFFFF] border-[#171717] text-[#171717]'
              : 'bg-[#FF4D4D] border-[#FF4D4D] text-[#FFFFFF]'
          }`}>
            <div className="flex items-center justify-between font-bold">
              <span>● INTEGRITY STATUS: {verification.status}</span>
              <span>VERIFIED: {new Date(verification.verified_at).toLocaleTimeString()}</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-1.5 p-2 bg-[#F4F1E8] text-[#171717] border border-[#D6D2C8]">
              <div>
                <span className="text-[#5E5E5E] block text-[8px]">OFF-CHAIN CALCULATED:</span>
                <span className="break-all font-bold">{verification.calculated_hash}</span>
              </div>
              <div>
                <span className="text-[#5E5E5E] block text-[8px]">BLOCKCHAIN ANCHORED:</span>
                <span className="break-all font-bold">{verification.anchored_hash}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Manifest Modal */}
      <EvidenceManifestModal
        isOpen={isManifestOpen}
        onClose={() => setIsManifestOpen(false)}
        manifest={manifest}
        evidenceId={activePackage.evidence_id}
      />
    </div>
  );
};
