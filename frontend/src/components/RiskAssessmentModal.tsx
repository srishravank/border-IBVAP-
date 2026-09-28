import React, { useState, useEffect } from 'react';
import {
  X,
  ShieldAlert,
  AlertTriangle,
  Info,
  CheckCircle2,
  Clock,
  RefreshCw,
  Sliders,
  Layers,
  FileCode,
  TrendingUp,
  MapPin
} from 'lucide-react';
import { api } from '../services/api';
import { RiskAssessment, RiskHistoryEntry, IncidentIntelligence } from '../types';

interface RiskAssessmentModalProps {
  incidentId: string;
  onClose: () => void;
  onOpenConfig?: () => void;
}

export const RiskAssessmentModal: React.FC<RiskAssessmentModalProps> = ({
  incidentId,
  onClose,
  onOpenConfig
}) => {
  const [activeTab, setActiveTab] = useState<'assessment' | 'history' | 'intelligence'>('assessment');
  const [assessment, setAssessment] = useState<RiskAssessment | null>(null);
  const [history, setHistory] = useState<RiskHistoryEntry[]>([]);
  const [intelligence, setIntelligence] = useState<IncidentIntelligence | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [recalculating, setRecalculating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async (forceRecalc = false) => {
    try {
      if (forceRecalc) setRecalculating(true);
      else setLoading(true);
      setError(null);

      const [riskData, histData, intelData] = await Promise.all([
        api.getIncidentRisk(incidentId, forceRecalc),
        api.getIncidentRiskHistory(incidentId),
        api.getIncidentIntelligence(incidentId)
      ]);

      setAssessment(riskData);
      setHistory(histData);
      setIntelligence(intelData);
    } catch (err: any) {
      setError(err.message || 'Failed to load risk assessment');
    } finally {
      setLoading(false);
      setRecalculating(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [incidentId]);

  const getRiskColor = (level: string) => {
    switch (level?.toUpperCase()) {
      case 'CRITICAL':
      case 'HIGH':
        return {
          bg: 'bg-rose-500/10 border-rose-500/30 text-[#FF4D4D]',
          badge: 'bg-rose-500/10 text-[#FF4D4D] border border-rose-500/30',
          bar: 'bg-[#FF4D4D]'
        };
      case 'MEDIUM':
        return {
          bg: 'bg-amber-500/10 border-amber-500/30 text-[#F5A623]',
          badge: 'bg-amber-500/10 text-[#F5A623] border border-amber-500/30',
          bar: 'bg-[#F5A623]'
        };
      default:
        return {
          bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-800 dark:text-[#C7FF3D]',
          badge: 'bg-[#C7FF3D]/10 text-emerald-800 dark:text-[#C7FF3D] border border-emerald-500/30',
          bar: 'bg-[#C7FF3D]'
        };
    }
  };

  const riskColors = getRiskColor(assessment?.risk_level || 'LOW');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="relative w-full max-w-5xl h-[88vh] flex flex-col bg-forensic-surface border border-forensic-border rounded shadow-2xl overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-forensic-border bg-forensic-elevated">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded bg-forensic-bg border border-forensic-border text-forensic-text">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-forensic-text uppercase tracking-widest font-mono">
                  Explainable Risk Assessment
                </h2>
                <span className="px-2 py-0.5 text-xs font-mono font-bold rounded bg-forensic-bg text-forensic-text border border-forensic-border">
                  {incidentId}
                </span>
                {assessment && (
                  <span className={`px-2 py-0.5 text-xs font-bold font-mono uppercase rounded ${riskColors.badge}`}>
                    {assessment.risk_level} RISK
                  </span>
                )}
              </div>
              <p className="text-xs text-forensic-muted font-mono mt-0.5">
                Subject: <span className="text-forensic-text font-bold">{assessment?.subject_id || 'N/A'}</span> • Phase 5 Intelligence Engine (Zero Black-Box Scoring)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => fetchData(true)}
              disabled={recalculating}
              className="px-3 py-1.5 text-xs font-mono font-bold rounded bg-forensic-bg hover:bg-forensic-elevated text-forensic-text border border-forensic-border flex items-center gap-1.5 transition"
              title="Force Recalculate Assessment"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${recalculating ? 'animate-spin' : ''}`} />
              {recalculating ? 'Evaluating...' : 'Recalculate'}
            </button>

            {onOpenConfig && (
              <button
                onClick={onOpenConfig}
                className="px-3 py-1.5 text-xs font-mono font-bold rounded bg-forensic-bg hover:bg-forensic-elevated text-forensic-text border border-forensic-border flex items-center gap-1.5 transition"
              >
                <Sliders className="w-3.5 h-3.5" />
                Config Weights
              </button>
            )}

            <button
              onClick={onClose}
              className="p-1.5 rounded text-forensic-muted hover:text-forensic-text hover:bg-forensic-bg transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 px-6 border-b border-forensic-border bg-forensic-surface">
          <button
            onClick={() => setActiveTab('assessment')}
            className={`flex items-center gap-2 px-4 py-3 text-xs font-mono font-bold border-b-2 transition ${
              activeTab === 'assessment'
                ? 'border-forensic-text text-forensic-text'
                : 'border-transparent text-forensic-muted hover:text-forensic-text'
            }`}
          >
            <ShieldAlert className="w-4 h-4" />
            Factor Assessment
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center gap-2 px-4 py-3 text-xs font-mono font-bold border-b-2 transition ${
              activeTab === 'history'
                ? 'border-forensic-text text-forensic-text'
                : 'border-transparent text-forensic-muted hover:text-forensic-text'
            }`}
          >
            <TrendingUp className="w-4 h-4" />
            Risk History ({history.length})
          </button>
          <button
            onClick={() => setActiveTab('intelligence')}
            className={`flex items-center gap-2 px-4 py-3 text-xs font-mono font-bold border-b-2 transition ${
              activeTab === 'intelligence'
                ? 'border-forensic-text text-forensic-text'
                : 'border-transparent text-forensic-muted hover:text-forensic-text'
            }`}
          >
            <FileCode className="w-4 h-4" />
            Phase 6 Intelligence Object
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 p-6 overflow-y-auto bg-forensic-bg">
          {loading ? (
            <div className="h-full flex flex-col items-center justify-center gap-3 text-forensic-muted font-mono text-xs">
              <RefreshCw className="w-8 h-8 animate-spin" />
              <p>Synthesizing multi-factor explainable risk assessment...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded bg-rose-500/10 border border-rose-500/30 text-[#FF4D4D] flex items-center gap-3 font-mono text-xs">
              <AlertTriangle className="w-5 h-5 flex-shrink-0" />
              <p>{error}</p>
            </div>
          ) : assessment ? (
            <>
              {/* TAB 1: ASSESSMENT */}
              {activeTab === 'assessment' && (
                <div className="space-y-6">
                  {/* Score & Gauge Banner */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Overall Score */}
                    <div className="p-5 rounded bg-forensic-surface border border-forensic-border flex flex-col justify-between">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold uppercase tracking-wider text-forensic-muted font-mono">
                          Composite Risk Score
                        </span>
                        <span className="text-xs text-forensic-muted font-mono">{assessment.config_version}</span>
                      </div>
                      <div className="flex items-baseline gap-2 my-2 font-mono">
                        <span className="text-4xl font-extrabold text-forensic-text tracking-tight">
                          {assessment.score.toFixed(1)}
                        </span>
                        <span className="text-sm font-medium text-forensic-muted">/ 100</span>
                      </div>
                      <div className="w-full bg-forensic-bg h-2 rounded overflow-hidden border border-forensic-border">
                        <div
                          className={`h-full transition-all duration-500 ${riskColors.bar}`}
                          style={{ width: `${Math.min(100, Math.max(5, assessment.score))}%` }}
                        />
                      </div>
                    </div>

                    {/* Risk Level */}
                    <div className={`p-5 rounded border flex flex-col justify-between ${riskColors.bg}`}>
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold uppercase tracking-wider font-mono">
                          Threat Classification
                        </span>
                        <AlertTriangle className="w-4 h-4" />
                      </div>
                      <div className="text-3xl font-black tracking-wider uppercase my-2 font-mono">
                        {assessment.risk_level}
                      </div>
                      <p className="text-xs opacity-80 font-mono">
                        Evaluated across {assessment.factors.length} modular intelligence factors
                      </p>
                    </div>

                    {/* Confidence & Traceability */}
                    <div className="p-5 rounded bg-forensic-surface border border-forensic-border flex flex-col justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-forensic-muted font-mono">
                        Assessment Confidence
                      </span>
                      <div className="flex items-baseline gap-2 my-2 font-mono">
                        <span className="text-3xl font-bold text-forensic-text">
                          {(assessment.confidence * 100).toFixed(0)}%
                        </span>
                        <span className="text-xs text-emerald-700 dark:text-[#C7FF3D] font-bold">Multi-Frame Verified</span>
                      </div>
                      <p className="text-xs text-forensic-muted font-mono">
                        Updated {new Date(assessment.updated_at).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>

                  {/* Human-Readable Explanation Box */}
                  <div className="p-5 rounded bg-forensic-surface border border-forensic-border">
                    <div className="flex items-center gap-2 mb-2 text-forensic-text">
                      <Info className="w-4 h-4 text-forensic-muted" />
                      <span className="text-xs font-bold uppercase tracking-wider font-mono">
                        Why was this risk level assigned? (Explainable Narrative)
                      </span>
                    </div>
                    <p className="text-xs text-forensic-text leading-relaxed font-mono">
                      &quot;{assessment.explanation}&quot;
                    </p>
                  </div>

                  {/* Fact vs Assessment Table / Cards */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-xs font-bold text-forensic-text uppercase tracking-wider font-mono flex items-center gap-2">
                        <Layers className="w-4 h-4 text-forensic-muted" />
                        Verified Facts vs Risk Assessment Breakdown
                      </h3>
                      <span className="text-xs text-forensic-muted font-mono">
                        Strict separation of observed facts from assessment impact
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {assessment.evidence_checklist.map((item, idx) => (
                        <div
                          key={idx}
                          className="p-4 rounded bg-forensic-surface border border-forensic-border hover:border-forensic-text transition flex flex-col justify-between gap-2"
                        >
                          <div className="flex items-center justify-between font-mono">
                            <span className="text-xs font-bold text-forensic-text">
                              {item.factor_name}
                            </span>
                            <span
                              className={`px-2 py-0.5 text-xs font-mono font-bold rounded ${
                                item.contribution > 15
                                  ? 'bg-rose-500/10 text-[#FF4D4D] border border-rose-500/30'
                                  : item.contribution > 0
                                  ? 'bg-amber-500/10 text-[#F5A623] border border-amber-500/30'
                                  : 'bg-forensic-bg text-forensic-muted border border-forensic-border'
                              }`}
                            >
                              {item.assessment}
                            </span>
                          </div>

                          <div className="space-y-1 font-mono">
                            <div className="text-xs text-forensic-text">
                              <strong className="text-forensic-muted uppercase text-[10px] tracking-wide block">
                                Verified Fact:
                              </strong>
                              {item.fact}
                            </div>
                          </div>

                          <div className="flex items-center justify-between pt-2 border-t border-forensic-border text-[11px] text-forensic-muted font-mono">
                            <span>Confidence: {(item.confidence * 100).toFixed(0)}%</span>
                            {item.source_events && item.source_events.length > 0 && (
                              <span className="font-mono text-forensic-muted">
                                Sources: {item.source_events.join(', ')}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: RISK HISTORY */}
              {activeTab === 'history' && (
                <div className="space-y-4 font-mono">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-xs font-bold text-forensic-text uppercase tracking-wider">
                      Chronological Risk Progression
                    </h3>
                    <span className="text-xs text-forensic-muted">
                      Shows how risk evolved as successive multi-frame events were verified
                    </span>
                  </div>

                  {history.length === 0 ? (
                    <p className="text-xs text-forensic-muted text-center py-8">No historical risk records found.</p>
                  ) : (
                    <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-forensic-border">
                      {history.map((h, i) => {
                        const hColors = getRiskColor(h.risk_level);
                        return (
                          <div key={h.history_id || i} className="relative flex items-start gap-4">
                            <div className={`absolute -left-6 mt-1.5 w-3.5 h-3.5 rounded-full border-2 border-forensic-border ${hColors.bar}`} />
                            <div className="flex-1 p-4 rounded bg-forensic-surface border border-forensic-border">
                              <div className="flex items-center justify-between mb-1.5">
                                <div className="flex items-center gap-2">
                                  <span className={`px-2 py-0.5 text-xs font-bold rounded ${hColors.badge}`}>
                                    {h.risk_level}
                                  </span>
                                  <span className="text-xs font-bold text-forensic-text">
                                    Score: {h.score.toFixed(1)} / 100
                                  </span>
                                </div>
                                <span className="text-xs font-mono text-forensic-muted">
                                  {new Date(h.timestamp).toLocaleTimeString()}
                                </span>
                              </div>

                              {h.factors_summary && h.factors_summary.length > 0 && (
                                <div className="mt-2 pt-2 border-t border-forensic-border space-y-1">
                                  {h.factors_summary.map((f, fi) => (
                                    <div key={fi} className="text-xs text-forensic-text flex items-center justify-between">
                                      <span>• {f.name}: {f.evidence}</span>
                                      <span className="font-mono text-forensic-muted font-bold">+{f.contribution}pts</span>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {/* TAB 3: PHASE 6 INTELLIGENCE OBJECT */}
              {activeTab === 'intelligence' && (
                <div className="space-y-4 font-mono">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xs font-bold text-forensic-text uppercase tracking-wider">
                        Standardized Phase 6 Input Interface
                      </h3>
                      <p className="text-xs text-forensic-muted">
                        Structured intelligence payload consumed by downstream Command & Response
                      </p>
                    </div>
                    <button
                      onClick={() => navigator.clipboard.writeText(JSON.stringify(intelligence, null, 2))}
                      className="px-3 py-1.5 text-xs font-mono font-bold rounded bg-forensic-surface hover:bg-forensic-bg text-forensic-text border border-forensic-border transition"
                    >
                      Copy JSON
                    </button>
                  </div>

                  <pre className="p-4 rounded bg-forensic-surface border border-forensic-border text-xs font-mono text-forensic-text overflow-x-auto max-h-[500px]">
                    {JSON.stringify(intelligence, null, 2)}
                  </pre>
                </div>
              )}
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
};
