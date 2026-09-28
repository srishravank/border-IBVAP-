import React, { useState, useEffect } from 'react';
import {
  X,
  ShieldAlert,
  CheckCircle2,
  Clock,
  ArrowRight,
  Eye,
  Camera,
  MapPin,
  Share2,
  FileText,
  MessageSquare,
  History,
  Send,
  AlertTriangle,
  User,
  Sliders,
  Check,
  Compass,
  Car,
  ShieldCheck
} from 'lucide-react';
import {
  Incident,
  IncidentLifecycle,
  IncidentNarrative,
  RecommendedCamera,
  IncidentNote,
  OperatorAction,
  RiskAssessment,
  UserRole
} from '../types';
import { api } from '../services/api';
import { EvidenceTrustPanel } from './Evidence/EvidenceTrustPanel';

interface IncidentInvestigationModalProps {
  incidentId: string | null;
  currentRole: UserRole;
  currentOperatorId: string;
  onClose: () => void;
  onOpenIncidentGraph?: (incidentId: string) => void;
  onFocusCamera?: (cameraId: string) => void;
  onRefreshParent?: () => void;
}

export const IncidentInvestigationModal: React.FC<IncidentInvestigationModalProps> = ({
  incidentId,
  currentRole,
  currentOperatorId,
  onClose,
  onOpenIncidentGraph,
  onFocusCamera,
  onRefreshParent,
}) => {
  const [lifecycle, setLifecycle] = useState<IncidentLifecycle | null>(null);
  const [narrative, setNarrative] = useState<IncidentNarrative | null>(null);
  const [recommendedCameras, setRecommendedCameras] = useState<RecommendedCamera[]>([]);
  const [riskAssessment, setRiskAssessment] = useState<RiskAssessment | null>(null);
  const [notes, setNotes] = useState<IncidentNote[]>([]);
  const [actions, setActions] = useState<OperatorAction[]>([]);
  
  const [newNote, setNewNote] = useState<string>('');
  const [actionNotes, setActionNotes] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'RECOMMENDATIONS' | 'NOTES' | 'AUDIT' | 'EVIDENCE'>('OVERVIEW');

  // Load modal data
  const loadData = async () => {
    if (!incidentId) return;
    try {
      setLoading(true);
      const [lf, nar, recs, risk, nts, acts] = await Promise.all([
        api.getIncidentLifecycle(incidentId).catch(() => null),
        api.getIncidentNarrative(incidentId).catch(() => null),
        api.getRecommendedCameras(incidentId).catch(() => ({ recommended_cameras: [] })),
        api.getIncidentRisk(incidentId, false).catch(() => null),
        api.getIncidentNotes(incidentId).catch(() => []),
        api.getOperatorActions(incidentId, 50).catch(() => []),
      ]);

      if (lf) setLifecycle(lf);
      if (nar) setNarrative(nar);
      if (recs?.recommended_cameras) setRecommendedCameras(recs.recommended_cameras);
      if (risk) setRiskAssessment(risk);
      setNotes(nts);
      setActions(acts);
    } catch (err) {
      console.error('Failed to load incident investigation details:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [incidentId]);

  if (!incidentId) return null;

  // Handlers for state machine transitions
  const handleAcknowledge = async () => {
    try {
      await api.acknowledgeIncident(incidentId, currentOperatorId, currentRole, actionNotes || 'Operator acknowledged incident alert');
      setActionNotes('');
      await loadData();
      if (onRefreshParent) onRefreshParent();
    } catch (err: any) {
      alert(err.message || 'Failed to acknowledge incident');
    }
  };

  const handleInvestigate = async () => {
    try {
      await api.investigateIncident(incidentId, currentOperatorId, currentRole, actionNotes || 'Operator initiated formal SOC investigation');
      setActionNotes('');
      await loadData();
      if (onRefreshParent) onRefreshParent();
    } catch (err: any) {
      alert(err.message || 'Failed to start investigation');
    }
  };

  const handleClose = async () => {
    try {
      await api.closeIncident(incidentId, currentOperatorId, currentRole, actionNotes || 'Incident resolved and closed by operator');
      setActionNotes('');
      await loadData();
      if (onRefreshParent) onRefreshParent();
    } catch (err: any) {
      alert(err.message || 'Failed to close incident');
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNote.trim()) return;
    try {
      await api.addIncidentNote(incidentId, currentOperatorId, currentRole, newNote.trim());
      setNewNote('');
      const updatedNotes = await api.getIncidentNotes(incidentId);
      setNotes(updatedNotes);
      const updatedActs = await api.getOperatorActions(incidentId);
      setActions(updatedActs);
    } catch (err: any) {
      alert(err.message || 'Failed to add operator note');
    }
  };

  const getRiskLevelColor = (level?: string) => {
    switch (level) {
      case 'CRITICAL':
        return 'bg-rose-500/10 text-[#FF4D4D] border-rose-500/40';
      case 'HIGH':
        return 'bg-amber-500/10 text-[#F5A623] border-amber-500/40';
      case 'MEDIUM':
        return 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/30';
      default:
        return 'bg-emerald-500/10 text-emerald-800 dark:text-emerald-300 border-emerald-500/30';
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-forensic-surface border border-forensic-border rounded w-full max-w-5xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden font-sans">
        
        {/* Header Bar */}
        <div className="p-4 sm:p-5 bg-forensic-elevated border-b border-forensic-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded bg-rose-500/10 border border-rose-500/30 text-[#FF4D4D]">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-base font-bold font-mono text-forensic-text">
                  {incidentId}
                </span>
                <span className="px-2 py-0.5 rounded bg-forensic-bg text-forensic-text border border-forensic-border text-xs font-mono font-bold">
                  {lifecycle?.subject_id || 'UNKNOWN'}
                </span>
                {riskAssessment && (
                  <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold border ${getRiskLevelColor(riskAssessment.risk_level)}`}>
                    {riskAssessment.risk_level} ({riskAssessment.score.toFixed(1)})
                  </span>
                )}
                <span className="px-2 py-0.5 rounded bg-forensic-bg text-forensic-muted border border-forensic-border text-xs font-mono font-semibold">
                  STATUS: {lifecycle?.current_status || 'UNKNOWN'}
                </span>
              </div>
              <div className="text-xs text-forensic-muted font-mono mt-0.5 flex items-center gap-2">
                <span>SOC Command & Response Cockpit</span>
                <span>•</span>
                <span className="text-forensic-text font-bold">Operator: {currentOperatorId} ({currentRole})</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {onOpenIncidentGraph && (
              <button
                onClick={() => onOpenIncidentGraph(incidentId)}
                className="px-3 py-1.5 rounded bg-forensic-bg hover:bg-forensic-elevated text-forensic-text border border-forensic-border text-xs font-mono flex items-center gap-1.5 transition"
                title="View Full Graph Topology"
              >
                <Share2 className="w-3.5 h-3.5" />
                <span>Incident Graph</span>
              </button>
            )}

            <button
              onClick={onClose}
              className="p-1.5 rounded bg-forensic-bg hover:bg-forensic-elevated text-forensic-muted hover:text-forensic-text border border-forensic-border transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* 7-Stage Visual Lifecycle Stepper */}
        <div className="bg-forensic-bg px-4 py-3 border-b border-forensic-border">
          <div className="text-[10px] font-mono text-forensic-muted uppercase tracking-wider mb-2 font-semibold">
            7-STAGE INCIDENT RESPONSE LIFECYCLE
          </div>
          
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
            {lifecycle?.stages?.map((stage, idx) => {
              const isDone = stage.is_completed;
              const isCurr = stage.is_current;

              return (
                <div
                  key={stage.stage_name}
                  className={`p-2 rounded border text-xs font-mono transition flex flex-col justify-between ${
                    isCurr
                      ? 'bg-rose-500/10 border-[#FF4D4D] text-[#FF4D4D] shadow-sm ring-1 ring-rose-500/40'
                      : isDone
                      ? 'bg-[#C7FF3D]/10 border-emerald-500/30 text-emerald-800 dark:text-[#C7FF3D]'
                      : 'bg-forensic-surface border-forensic-border text-forensic-muted opacity-60'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-bold">
                      {idx + 1}. {stage.display_name}
                    </span>
                    {isDone ? (
                      <Check className="w-3.5 h-3.5 text-emerald-600 dark:text-[#C7FF3D]" />
                    ) : isCurr ? (
                      <span className="w-2 h-2 rounded-full bg-[#FF4D4D] animate-ping" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-forensic-border" />
                    )}
                  </div>
                  <div className="text-[9px] text-forensic-muted truncate">
                    {stage.completed_at
                      ? new Date(stage.completed_at).toLocaleTimeString()
                      : isCurr
                      ? 'ACTIVE'
                      : 'PENDING'}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Operator Lifecycle Transition Action Bar */}
        {lifecycle && lifecycle.current_status !== 'CLOSED' && (
          <div className="bg-forensic-elevated px-4 py-2.5 border-b border-forensic-border flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2">
            <div className="flex items-center gap-2 flex-1">
              <input
                type="text"
                placeholder="Optional action notes / decision rationale..."
                value={actionNotes}
                onChange={(e) => setActionNotes(e.target.value)}
                className="bg-forensic-bg border border-forensic-border rounded px-3 py-1.5 text-xs font-mono text-forensic-text placeholder-forensic-muted focus:outline-none focus:border-forensic-text flex-1"
              />
            </div>

            <div className="flex items-center gap-2 flex-wrap justify-end">
              {lifecycle.allowed_transitions.includes('ACKNOWLEDGED') && (
                <button
                  onClick={handleAcknowledge}
                  className="px-3 py-1.5 rounded bg-amber-600 hover:bg-amber-500 text-white font-mono text-xs font-bold transition flex items-center gap-1.5 shadow-sm"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Acknowledge</span>
                </button>
              )}

              {lifecycle.allowed_transitions.includes('INVESTIGATING') && (
                <button
                  onClick={handleInvestigate}
                  className="px-3 py-1.5 rounded bg-[#171717] dark:bg-[#F4F1E8] text-[#F4F1E8] dark:text-[#171717] hover:opacity-90 font-mono text-xs font-bold transition flex items-center gap-1.5 shadow-sm"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Start Investigation</span>
                </button>
              )}

              {lifecycle.allowed_transitions.includes('CLOSED') && (
                <button
                  onClick={handleClose}
                  className="px-3 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-bold transition flex items-center gap-1.5 shadow-sm"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>Close Incident</span>
                </button>
              )}
            </div>
          </div>
        )}

        {/* Cockpit Navigation Tabs */}
        <div className="bg-forensic-surface px-4 pt-2 border-b border-forensic-border flex items-center gap-2">
          <button
            onClick={() => setActiveTab('OVERVIEW')}
            className={`px-3 py-2 text-xs font-mono font-bold border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'OVERVIEW'
                ? 'border-[#FF4D4D] text-[#FF4D4D]'
                : 'border-transparent text-forensic-muted hover:text-forensic-text'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Narrative & Risk</span>
          </button>

          <button
            onClick={() => setActiveTab('RECOMMENDATIONS')}
            className={`px-3 py-2 text-xs font-mono font-bold border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'RECOMMENDATIONS'
                ? 'border-forensic-text text-forensic-text'
                : 'border-transparent text-forensic-muted hover:text-forensic-text'
            }`}
          >
            <Camera className="w-3.5 h-3.5" />
            <span>Forward Cameras ({recommendedCameras.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('NOTES')}
            className={`px-3 py-2 text-xs font-mono font-bold border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'NOTES'
                ? 'border-forensic-text text-forensic-text'
                : 'border-transparent text-forensic-muted hover:text-forensic-text'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Operator Notes ({notes.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('AUDIT')}
            className={`px-3 py-2 text-xs font-mono font-bold border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'AUDIT'
                ? 'border-[#F5A623] text-[#F5A623]'
                : 'border-transparent text-forensic-muted hover:text-forensic-text'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>Audit Trail ({actions.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('EVIDENCE')}
            className={`px-3 py-2 text-xs font-mono font-bold border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'EVIDENCE'
                ? 'border-emerald-600 text-emerald-700 dark:text-[#C7FF3D]'
                : 'border-transparent text-forensic-muted hover:text-forensic-text'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Evidence Trust & Blockchain</span>
          </button>
        </div>

        {/* Tab Content Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 bg-forensic-bg">
          {activeTab === 'EVIDENCE' && (
            <EvidenceTrustPanel
              incidentId={incidentId}
              operatorId={currentOperatorId}
              role={currentRole}
            />
          )}

          {activeTab === 'OVERVIEW' && (
            <div className="space-y-6">
              
              {/* Machine-Generated Explainable Narrative */}
              {narrative && (
                <div className="bg-forensic-surface border border-forensic-border rounded p-4 space-y-3">
                  <div className="flex items-center justify-between border-b border-forensic-border pb-2">
                    <h4 className="text-xs font-bold text-forensic-text uppercase font-mono flex items-center gap-1.5">
                      <FileText className="w-4 h-4 text-forensic-muted" />
                      EXPLAINABLE OPERATIONAL NARRATIVE
                    </h4>
                    <span className="text-[10px] font-mono text-forensic-muted">
                      Objective AI Decision Support
                    </span>
                  </div>

                  <div className="space-y-2 text-xs font-mono text-forensic-text">
                    <p className="font-semibold">
                      {narrative.summary}
                    </p>

                    {narrative.timeline_narrative && narrative.timeline_narrative.length > 0 && (
                      <div className="bg-forensic-bg p-3 rounded border border-forensic-border space-y-1.5">
                        <span className="text-[10px] text-forensic-muted uppercase font-bold block">
                          CHRONOLOGICAL OBSERVATION SEQUENCE:
                        </span>
                        {narrative.timeline_narrative.map((line, i) => (
                          <div key={i} className="flex items-start gap-2 text-[11px] text-forensic-text">
                            <span className="text-forensic-muted font-bold">•</span>
                            <span>{line}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {narrative.risk_narrative && (
                      <div className="p-2.5 rounded bg-rose-500/10 border border-rose-500/30 text-[11px] text-[#FF4D4D]">
                        <span className="font-bold uppercase block text-[10px] mb-0.5">
                          RISK SYNTHESIS:
                        </span>
                        {narrative.risk_narrative}
                      </div>
                    )}

                    {narrative.vehicle_narrative && (
                      <div className="p-2.5 rounded bg-amber-500/10 border border-amber-500/30 text-[11px] text-[#F5A623] flex items-start gap-2">
                        <Car className="w-4 h-4 text-[#F5A623] flex-shrink-0 mt-0.5" />
                        <div>
                          <span className="font-bold uppercase block text-[10px] mb-0.5">
                            VEHICLE CONTEXT:
                          </span>
                          {narrative.vehicle_narrative}
                        </div>
                      </div>
                    )}

                    <div className="p-2.5 rounded bg-forensic-elevated border border-forensic-border text-[11px] text-forensic-text">
                      <span className="font-bold uppercase block text-[10px] mb-0.5 text-forensic-muted">
                        RECOMMENDED OPERATOR ACTION:
                      </span>
                      {narrative.recommendation}
                    </div>
                  </div>
                </div>
              )}

              {/* Explainable Risk Factors Breakdown */}
              {riskAssessment && (
                <div className="bg-forensic-surface border border-forensic-border rounded p-4 space-y-3">
                  <div className="flex items-center justify-between border-b border-forensic-border pb-2">
                    <h4 className="text-xs font-bold text-forensic-text uppercase font-mono flex items-center gap-1.5">
                      <Sliders className="w-4 h-4 text-forensic-muted" />
                      RISK FACTOR CONTRIBUTION BREAKDOWN
                    </h4>
                    <span className="text-[10px] font-mono text-forensic-muted">
                      Config Version: {riskAssessment.config_version}
                    </span>
                  </div>

                  <div className="space-y-2">
                    {riskAssessment.factors?.map((f) => (
                      <div
                        key={f.factor_id}
                        className="bg-forensic-bg p-2.5 rounded border border-forensic-border flex flex-col gap-1 text-xs font-mono"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-forensic-text">
                            {f.factor_name}
                          </span>
                          <span className="text-[#FF4D4D] font-bold">
                            +{f.contribution.toFixed(1)} pts
                          </span>
                        </div>
                        <p className="text-[11px] text-forensic-muted italic">
                          {f.evidence}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            </div>
          )}

          {activeTab === 'RECOMMENDATIONS' && (
            <div className="space-y-4">
              <div className="text-xs font-mono text-forensic-muted">
                The AI topological tracking engine recommends monitoring the following forward cameras based on spatial connectivity and trajectory heading vectors:
              </div>

              {recommendedCameras.length === 0 ? (
                <div className="p-8 text-center text-forensic-muted font-mono text-xs flex flex-col items-center justify-center gap-2">
                  <Camera className="w-8 h-8 opacity-40" />
                  <span>NO IMMEDIATE DOWNSTREAM CAMERAS RECORDED IN TOPOLOGY</span>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {recommendedCameras.map((rec) => (
                    <div
                      key={rec.camera_id}
                      className="bg-forensic-surface border border-forensic-border hover:border-forensic-text rounded p-4 flex flex-col justify-between gap-3 transition"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded bg-forensic-bg text-forensic-text border border-forensic-border font-mono text-xs font-bold">
                            {rec.camera_id}
                          </span>
                          <span className="font-bold text-xs text-forensic-text font-mono">
                            {rec.camera_name}
                          </span>
                        </div>
                        <span className="text-[10px] font-mono text-forensic-muted bg-forensic-bg px-2 py-0.5 rounded border border-forensic-border">
                          {rec.sector}
                        </span>
                      </div>

                      <div className="bg-forensic-bg p-2.5 rounded border border-forensic-border text-xs font-mono space-y-1">
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-forensic-muted">Heading & Transit:</span>
                          <span className="text-forensic-text font-bold">
                            {rec.direction} • ~{rec.transition_time_estimate_sec}s ({rec.distance_meters}m)
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-forensic-muted">Confidence:</span>
                          <span className="text-emerald-700 dark:text-[#C7FF3D] font-bold">
                            {(rec.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="text-[11px] text-forensic-muted pt-1 border-t border-forensic-border">
                          {rec.reason}
                        </p>
                      </div>

                      <div className="flex items-center justify-end">
                        {onFocusCamera && (
                          <button
                            onClick={() => {
                              onFocusCamera(rec.camera_id);
                              onClose();
                            }}
                            className="px-3 py-1.5 bg-[#171717] dark:bg-[#F4F1E8] text-[#F4F1E8] dark:text-[#171717] hover:opacity-90 rounded text-xs font-mono font-bold flex items-center gap-1.5 transition shadow-sm"
                          >
                            <Camera className="w-3.5 h-3.5" />
                            <span>Focus Camera Feed</span>
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'NOTES' && (
            <div className="space-y-4">
              {/* Add note input */}
              <form onSubmit={handleAddNote} className="flex gap-2">
                <input
                  type="text"
                  placeholder="Type an operator investigation note..."
                  value={newNote}
                  onChange={(e) => setNewNote(e.target.value)}
                  className="bg-forensic-surface border border-forensic-border rounded px-3 py-2 text-xs font-mono text-forensic-text placeholder-forensic-muted focus:outline-none focus:border-forensic-text flex-1"
                />
                <button
                  type="submit"
                  className="px-4 py-2 bg-[#171717] dark:bg-[#F4F1E8] text-[#F4F1E8] dark:text-[#171717] font-mono text-xs font-bold rounded transition flex items-center gap-1.5 shadow-sm"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Add Note</span>
                </button>
              </form>

              {/* Notes list */}
              <div className="space-y-2">
                {notes.length === 0 ? (
                  <div className="p-8 text-center text-forensic-muted font-mono text-xs">
                    NO OPERATOR NOTES RECORDED YET
                  </div>
                ) : (
                  notes.map((n) => (
                    <div
                      key={n.note_id}
                      className="bg-forensic-surface border border-forensic-border rounded p-3 flex flex-col gap-1 text-xs font-mono"
                    >
                      <div className="flex items-center justify-between text-[11px] text-forensic-muted">
                        <div className="flex items-center gap-1.5">
                          <User className="w-3.5 h-3.5 text-forensic-text" />
                          <span className="font-bold text-forensic-text">{n.operator_id}</span>
                          <span className="px-1.5 py-0.2 bg-forensic-bg rounded text-[10px] text-forensic-muted border border-forensic-border">
                            {n.role}
                          </span>
                        </div>
                        <span>{new Date(n.timestamp).toLocaleString()}</span>
                      </div>
                      <p className="text-forensic-text pt-1">
                        {n.note}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {activeTab === 'AUDIT' && (
            <div className="space-y-3">
              <div className="text-xs font-mono text-forensic-muted">
                Immutable, timestamped audit trail of all operator state transitions, acknowledgements, and investigation decisions:
              </div>

              <div className="divide-y divide-forensic-border border border-forensic-border rounded overflow-hidden bg-forensic-surface">
                {actions.length === 0 ? (
                  <div className="p-8 text-center text-forensic-muted font-mono text-xs">
                    NO OPERATOR ACTIONS RECORDED
                  </div>
                ) : (
                  actions.map((act) => (
                    <div key={act.action_id} className="p-3 flex items-start justify-between gap-3 text-xs font-mono">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-[#F5A623]">{act.action}</span>
                          <span className="text-[10px] text-forensic-muted">by</span>
                          <span className="font-bold text-forensic-text">{act.operator_id}</span>
                          <span className="px-1.5 py-0.2 bg-forensic-bg rounded text-[10px] text-forensic-muted border border-forensic-border">
                            {act.role}
                          </span>
                        </div>
                        {act.notes && (
                          <p className="text-[11px] text-forensic-muted italic">
                            &quot;{act.notes}&quot;
                          </p>
                        )}
                      </div>
                      <span className="text-[10px] text-forensic-muted flex-shrink-0">
                        {new Date(act.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};
