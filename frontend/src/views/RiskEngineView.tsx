import React, { useState, useEffect } from 'react';
import {
  Incident,
  RiskAssessment,
  RiskConfig,
  SectorRisk,
} from '../types';
import { api } from '../services/api';
import {
  Flame,
  Sliders,
  Sparkles,
  Save,
  ArrowDown,
  Layers,
  Camera,
  User,
  ShieldAlert,
  Lock,
  Crosshair,
} from 'lucide-react';

interface RiskEngineViewProps {
  incidents: Incident[];
  sectorRisks: SectorRisk[];
  onOpenRiskConfig: () => void;
  onSelectIncident: (incidentId: string) => void;
  onRefresh: () => void;
}

export const RiskEngineView: React.FC<RiskEngineViewProps> = ({
  incidents,
  onOpenRiskConfig,
  onRefresh,
}) => {
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>(
    incidents.length > 0 ? incidents[0].incident_id : ''
  );
  const [assessment, setAssessment] = useState<RiskAssessment | null>(null);
  const [weights, setWeights] = useState<Record<string, number>>({
    restricted_zone: 20,
    fence_crossing: 25,
    night_movement: 15,
    persistent_trajectory: 15,
    vehicle_correlation: 10,
    loitering: 15,
  });
  const [isSavingConfig, setIsSavingConfig] = useState<boolean>(false);

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const c = await api.getRiskConfig();
        if (c.weights) setWeights(c.weights);
      } catch (e) {
        console.error(e);
      }
    };
    loadConfig();
  }, []);

  useEffect(() => {
    if (!selectedIncidentId) {
      if (incidents.length > 0) setSelectedIncidentId(incidents[0].incident_id);
      return;
    }

    let isMounted = true;
    const loadAssessment = async () => {
      try {
        const a = await api.getIncidentRisk(selectedIncidentId);
        if (isMounted) setAssessment(a);
      } catch (e) {
        console.error('Error loading risk assessment:', e);
      }
    };
    loadAssessment();

    return () => {
      isMounted = false;
    };
  }, [selectedIncidentId, incidents]);

  const handleSaveWeights = async () => {
    try {
      setIsSavingConfig(true);
      await api.updateRiskConfig({ weights });
      onRefresh();
      alert('Risk weights updated successfully!');
    } catch (e: any) {
      alert(e.message || 'Failed to update risk config');
    } finally {
      setIsSavingConfig(false);
    }
  };

  const activeInc = incidents.find(i => i.incident_id === selectedIncidentId);
  const camId = activeInc?.cameras_involved?.[0] || 'CAM-03';
  const trackId = 'TRACK-042';
  const zoneName = 'ZONE C (RIVERLINE)';
  const evidenceCode = 'EVT-029';
  const blockNum = 'BLOCK 0842';

  return (
    <div className="space-y-4 font-sans">
      {/* Header Toolbar */}
      <div className="bg-[#ECE9E0] border border-[#D6D2C8] rounded-sm p-3.5 shadow-none flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Flame className="w-4 h-4 text-[#171717]" />
            <div>
              <h2 className="text-xs font-bold text-[#171717] uppercase tracking-wider font-mono">
                EXPLAINABLE RISK ENGINE & THREAT SURFACE TOPOLOGY
              </h2>
              <p className="text-[10px] text-[#5E5E5E] font-mono">
                DETERMINISTIC EVIDENCE GRAPH • CAMERA → TRACK → ZONE → INCIDENT → BLOCKCHAIN
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap font-mono text-xs">
          <div className="flex items-center gap-1.5 bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm px-2 py-1">
            <span className="text-[10px] text-[#5E5E5E]">INCIDENT:</span>
            <select
              value={selectedIncidentId}
              onChange={(e) => setSelectedIncidentId(e.target.value)}
              className="bg-transparent text-[#171717] font-bold focus:outline-none cursor-pointer border-none p-0 text-xs"
            >
              {incidents.map((i) => (
                <option key={i.incident_id} value={i.incident_id}>
                  {i.incident_id} ({i.subject_id})
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={onOpenRiskConfig}
            className="flex items-center gap-1 px-2.5 py-1 bg-[#171717] hover:bg-[#292929] text-[#F4F1E8] rounded-sm text-xs font-semibold transition"
          >
            <Sliders className="w-3.5 h-3.5 text-[#C7FF3D]" />
            <span>ADVANCED CONFIG</span>
          </button>
        </div>
      </div>

      {/* Connected Threat Surface Node Flow */}
      <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-4 font-mono">
        <div className="flex items-center justify-between border-b border-[#ECE9E0] pb-2 mb-3">
          <span className="text-xs font-bold text-[#171717] uppercase">
            THREAT SURFACE RELATIONSHIP GRAPH // FORENSIC CAUSALITY CHAIN
          </span>
          <span className="text-[10px] text-[#5E5E5E]">6-STEP CORRELATION VECTOR</span>
        </div>

        <div className="flex flex-col md:flex-row items-center justify-between gap-2 p-3 bg-[#F4F1E8] rounded-sm border border-[#D6D2C8] text-xs">
          {/* Node 1: Camera */}
          <div className="flex flex-col items-center p-2.5 bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm min-w-[110px]">
            <Camera className="w-4 h-4 text-[#171717] mb-1" />
            <span className="text-[8px] text-[#8A877E] uppercase">SOURCE NODE</span>
            <span className="font-bold text-[#171717]">{camId}</span>
          </div>

          <span className="text-[#8A877E] font-bold hidden md:inline">────▶</span>
          <ArrowDown className="w-4 h-4 text-[#8A877E] md:hidden" />

          {/* Node 2: Track */}
          <div className="flex flex-col items-center p-2.5 bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm min-w-[110px]">
            <User className="w-4 h-4 text-[#171717] mb-1" />
            <span className="text-[8px] text-[#8A877E] uppercase">AI TRACK</span>
            <span className="font-bold text-[#171717]">{trackId}</span>
          </div>

          <span className="text-[#8A877E] font-bold hidden md:inline">────▶</span>
          <ArrowDown className="w-4 h-4 text-[#8A877E] md:hidden" />

          {/* Node 3: Zone */}
          <div className="flex flex-col items-center p-2.5 bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm min-w-[110px]">
            <Layers className="w-4 h-4 text-[#171717] mb-1" />
            <span className="text-[8px] text-[#8A877E] uppercase">VIRTUAL FENCE</span>
            <span className="font-bold text-[#171717]">{zoneName}</span>
          </div>

          <span className="text-[#8A877E] font-bold hidden md:inline">────▶</span>
          <ArrowDown className="w-4 h-4 text-[#8A877E] md:hidden" />

          {/* Node 4: Incident */}
          <div className="flex flex-col items-center p-2.5 bg-[#FF4D4D] text-[#FFFFFF] rounded-sm min-w-[110px]">
            <ShieldAlert className="w-4 h-4 mb-1" />
            <span className="text-[8px] opacity-90 uppercase">INCIDENT</span>
            <span className="font-bold">{selectedIncidentId || 'EVT-029'}</span>
          </div>

          <span className="text-[#8A877E] font-bold hidden md:inline">────▶</span>
          <ArrowDown className="w-4 h-4 text-[#8A877E] md:hidden" />

          {/* Node 5: Evidence */}
          <div className="flex flex-col items-center p-2.5 bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm min-w-[110px]">
            <Crosshair className="w-4 h-4 text-[#171717] mb-1" />
            <span className="text-[8px] text-[#8A877E] uppercase">EVIDENCE PKG</span>
            <span className="font-bold text-[#171717]">{evidenceCode}</span>
          </div>

          <span className="text-[#8A877E] font-bold hidden md:inline">────▶</span>
          <ArrowDown className="w-4 h-4 text-[#8A877E] md:hidden" />

          {/* Node 6: Blockchain */}
          <div className="flex flex-col items-center p-2.5 bg-[#171717] text-[#C7FF3D] rounded-sm min-w-[110px]">
            <Lock className="w-4 h-4 mb-1" />
            <span className="text-[8px] opacity-90 uppercase">IMMUTABLE ANCHOR</span>
            <span className="font-bold">{blockNum}</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Factor Breakdown & Weight Tuning */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 items-start font-mono">
        {/* Left 2 Cols: Selected Incident Score & Factor Breakdown */}
        <div className="xl:col-span-2 space-y-4">
          {assessment ? (
            <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-4 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#ECE9E0] pb-3">
                <div>
                  <span className="text-[10px] text-[#5E5E5E] font-bold block">
                    RISK SYNTHESIS BREAKDOWN
                  </span>
                  <h3 className="text-sm font-bold text-[#171717]">
                    INCIDENT {assessment.incident_id} (SUBJECT {assessment.subject_id})
                  </h3>
                  <p className="text-[10px] text-[#5E5E5E] mt-0.5">
                    CONFIG VERSION: {assessment.config_version} • CONFIDENCE: {(assessment.confidence * 100).toFixed(0)}%
                  </p>
                </div>

                <div className="p-3 bg-[#F4F1E8] border border-[#D6D2C8] rounded-sm flex flex-col items-center min-w-[120px]">
                  <span className="text-[8px] text-[#5E5E5E] uppercase font-bold">
                    RISK LEVEL
                  </span>
                  <span className={`text-lg font-bold ${
                    assessment.risk_level === 'CRITICAL' || assessment.risk_level === 'HIGH'
                      ? 'text-[#C53030]'
                      : 'text-[#B45309]'
                  }`}>
                    {assessment.risk_level}
                  </span>
                  <span className="text-xs font-bold text-[#171717]">
                    {assessment.score.toFixed(1)} / 100 PTS
                  </span>
                </div>
              </div>

              {/* Natural Language Justification */}
              <div className="bg-[#F4F1E8] border border-[#D6D2C8] rounded-sm p-3 space-y-1">
                <span className="text-[11px] font-bold text-[#171717] flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5 text-[#171717]" />
                  OBJECTIVE FORENSIC EXPLAINABILITY
                </span>
                <p className="text-[11px] text-[#171717] leading-relaxed">
                  {assessment.explanation}
                </p>
              </div>

              {/* Contributing Risk Factors */}
              <div className="space-y-2">
                <span className="text-xs font-bold text-[#171717] uppercase block">
                  CONTRIBUTING RISK FACTORS ({assessment.factors?.length || 0})
                </span>

                <div className="space-y-1.5">
                  {assessment.factors?.map((f) => (
                    <div
                      key={f.factor_id}
                      className="bg-[#F4F1E8] border border-[#D6D2C8] rounded-sm p-2.5 space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-[#FF4D4D]" />
                          <span className="font-bold text-xs text-[#171717]">
                            {f.factor_name}
                          </span>
                        </div>
                        <span className="px-1.5 py-0.2 bg-[#FF4D4D] text-[#FFFFFF] rounded-sm font-bold text-[9px]">
                          +{f.contribution} PTS
                        </span>
                      </div>

                      <p className="text-[10px] text-[#5E5E5E] pl-3">
                        EVIDENCE: {f.evidence}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-12 text-center text-[#5E5E5E] text-xs">
              No active incident selected.
            </div>
          )}
        </div>

        {/* Right 1 Col: Live Weight Tuner */}
        <div className="xl:col-span-1 space-y-4">
          <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-3.5 space-y-3">
            <div className="flex items-center justify-between border-b border-[#ECE9E0] pb-2">
              <span className="text-xs font-bold text-[#171717] uppercase flex items-center gap-1">
                <Sliders className="w-3.5 h-3.5 text-[#171717]" />
                LIVE WEIGHT TUNER
              </span>
              <span className="text-[9px] text-[#5E5E5E]">OPERATIONAL</span>
            </div>

            <div className="space-y-3 text-xs">
              {Object.entries(weights).map(([key, val]) => (
                <div key={key} className="space-y-1">
                  <div className="flex justify-between text-[11px]">
                    <span className="text-[#5E5E5E] uppercase text-[10px]">
                      {key.replace('_', ' ')}
                    </span>
                    <span className="text-[#171717] font-bold">+{val} PTS</span>
                  </div>
                  <input
                    type="range"
                    min="5"
                    max="50"
                    step="5"
                    value={val}
                    onChange={(e) =>
                      setWeights({ ...weights, [key]: parseInt(e.target.value, 10) })
                    }
                    className="w-full accent-[#171717] cursor-pointer h-1 bg-[#D6D2C8] rounded-none"
                  />
                </div>
              ))}
            </div>

            <div className="pt-2 border-t border-[#ECE9E0]">
              <button
                onClick={handleSaveWeights}
                disabled={isSavingConfig}
                className="w-full py-1.5 bg-[#171717] hover:bg-[#292929] text-[#F4F1E8] rounded-sm text-xs font-semibold transition flex items-center justify-center gap-1"
              >
                <Save className="w-3.5 h-3.5 text-[#C7FF3D]" />
                <span>{isSavingConfig ? 'APPLYING...' : 'APPLY WEIGHTS'}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
