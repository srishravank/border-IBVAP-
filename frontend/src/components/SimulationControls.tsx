import React, { useState } from 'react';
import { Unplug, Zap, CheckCircle2, Compass, ShieldAlert, RotateCcw, Activity } from 'lucide-react';
import { Camera } from '../types';
import { api } from '../services/api';

interface SimulationControlsProps {
  cameras: Camera[];
  onRefresh: () => void;
  onSelectSubject?: (subjectId: string) => void;
}

export const SimulationControls: React.FC<SimulationControlsProps> = ({ onRefresh, onSelectSubject }) => {
  const [demoLoading, setDemoLoading] = useState(false);
  const [activeScenario, setActiveScenario] = useState<string>('01 / BASELINE PATROL');
  const [activeRisk, setActiveRisk] = useState<'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'>('LOW');

  const handleSimulateDisconnect = async () => {
    try {
      await api.updateCamera('CAM-03', {
        source: 'data/videos/non_existent_stream.mp4',
      });
      onRefresh();
    } catch (e) {
      console.error(e);
    }
  };

  const handleRestoreCam3 = async () => {
    try {
      await api.updateCamera('CAM-03', {
        source: 'data/videos/camera03.mp4',
      });
      onRefresh();
    } catch (e) {
      console.error(e);
    }
  };

  const handleRunJourneyDemo = async () => {
    setDemoLoading(true);
    try {
      setActiveScenario('04 / CROSS-CAMERA JOURNEY');
      setActiveRisk('MEDIUM');
      const res = await api.runDemoJourney();
      onRefresh();
      if (onSelectSubject && res.subject_id) {
        onSelectSubject(res.subject_id);
      }
    } catch (e) {
      console.error('Demo journey error:', e);
    } finally {
      setDemoLoading(false);
    }
  };

  const handleRunFalseMatchDemo = async () => {
    setDemoLoading(true);
    try {
      setActiveScenario('05 / FALSE MATCH REJECTION');
      setActiveRisk('LOW');
      const res = await api.runDemoFalseMatch();
      onRefresh();
      alert(`[RE-ID ENGINE DETERMINISTIC REJECTION RESULT]\n\n• CAM-01 Subject: ${res.subject_cam01}\n• CAM-04 Subject: ${res.subject_cam04}\n• Match Decision: ${res.are_linked ? 'LINKED (Error)' : 'REJECTED (Validated)'}\n\nEvidence Rule Breakdown:\n${res.rejection_reasons.map((r: string) => `• ${r}`).join('\n')}`);
    } catch (e) {
      console.error('False match demo error:', e);
    } finally {
      setDemoLoading(false);
    }
  };

  const handleResetDemo = async () => {
    try {
      setActiveScenario('01 / BASELINE PATROL');
      setActiveRisk('LOW');
      await api.resetDemoState();
      onRefresh();
    } catch (e) {
      console.error('Reset demo error:', e);
    }
  };

  const handleScenario = async (scenNum: number, label: string, risk: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL') => {
    setDemoLoading(true);
    try {
      setActiveScenario(label);
      setActiveRisk(risk);
      const res = await api.runScenario(scenNum);
      onRefresh();
      if (onSelectSubject && res.subject_id) {
        onSelectSubject(res.subject_id);
      }
    } catch (e) {
      console.error('Scenario error:', e);
    } finally {
      setDemoLoading(false);
    }
  };

  return (
    <div className="bg-[#ECE9E0] border border-[#D6D2C8] rounded-sm p-3 shadow-none space-y-2.5 font-sans">
      {/* Simulation Masthead */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#D6D2C8] pb-2">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 font-mono font-bold text-xs text-[#171717]">
            <Activity className="w-3.5 h-3.5 text-[#171717]" />
            <span>SIMULATION & TEST ENGINE // SCENARIO INJECTION</span>
          </div>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs">
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-[#5E5E5E]">ACTIVE:</span>
            <span className="font-bold text-[#171717]">{activeScenario}</span>
          </div>
          <span className="text-[#D6D2C8]">|</span>
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-[#5E5E5E]">THREAT LEVEL:</span>
            <span className={`font-bold text-[10px] px-1.5 py-0.2 rounded-sm ${
              activeRisk === 'CRITICAL' || activeRisk === 'HIGH'
                ? 'bg-[#FF4D4D] text-[#FFFFFF]'
                : activeRisk === 'MEDIUM'
                ? 'bg-[#F5A623] text-[#171717]'
                : 'bg-[#171717] text-[#C7FF3D]'
            }`}>
              {activeRisk}
            </span>
          </div>
        </div>
      </div>

      {/* Scenario Controls Grid */}
      <div className="flex flex-wrap items-center gap-1.5 font-mono text-xs">
        {/* Scenario 1: Normal */}
        <button
          onClick={() => handleScenario(1, '01 / NORMAL PATROL', 'LOW')}
          disabled={demoLoading}
          className="px-2.5 py-1 bg-[#FFFFFF] hover:bg-[#171717] hover:text-[#C7FF3D] text-[#171717] border border-[#D6D2C8] rounded-sm font-semibold transition"
        >
          01 / NORMAL
        </button>

        {/* Scenario 2: Zone Entry */}
        <button
          onClick={() => handleScenario(2, '02 / ZONE ENTRY', 'MEDIUM')}
          disabled={demoLoading}
          className="px-2.5 py-1 bg-[#FFFFFF] hover:bg-[#171717] hover:text-[#F5A623] text-[#171717] border border-[#D6D2C8] rounded-sm font-semibold transition"
        >
          02 / ZONE ENTRY
        </button>

        {/* Scenario 3: Night Intrusion */}
        <button
          onClick={() => handleScenario(3, '03 / NIGHT INTRUSION', 'HIGH')}
          disabled={demoLoading}
          className="px-2.5 py-1 bg-[#FFFFFF] hover:bg-[#FF4D4D] hover:text-[#FFFFFF] text-[#171717] border border-[#D6D2C8] rounded-sm font-semibold transition flex items-center gap-1"
        >
          <ShieldAlert className="w-3 h-3 text-[#FF4D4D]" />
          <span>03 / NIGHT INTRUSION</span>
        </button>

        {/* Scenario 4: Cross Camera */}
        <button
          onClick={handleRunJourneyDemo}
          disabled={demoLoading}
          className="px-2.5 py-1 bg-[#FFFFFF] hover:bg-[#171717] hover:text-[#C7FF3D] text-[#171717] border border-[#D6D2C8] rounded-sm font-semibold transition flex items-center gap-1"
        >
          <Compass className="w-3 h-3 text-[#171717]" />
          <span>04 / CROSS-CAMERA</span>
        </button>

        {/* Scenario 5: False Match */}
        <button
          onClick={handleRunFalseMatchDemo}
          disabled={demoLoading}
          className="px-2.5 py-1 bg-[#FFFFFF] hover:bg-[#171717] hover:text-[#C7FF3D] text-[#171717] border border-[#D6D2C8] rounded-sm font-semibold transition"
        >
          05 / FALSE MATCH
        </button>

        {/* Scenario 6: Multi Factor */}
        <button
          onClick={() => handleScenario(6, '06 / MULTI-FACTOR INCIDENT', 'CRITICAL')}
          disabled={demoLoading}
          className="px-2.5 py-1 bg-[#FFFFFF] hover:bg-[#FF4D4D] hover:text-[#FFFFFF] text-[#171717] border border-[#D6D2C8] rounded-sm font-semibold transition flex items-center gap-1"
        >
          <Zap className="w-3 h-3 text-[#FF4D4D]" />
          <span>06 / MULTI-FACTOR</span>
        </button>

        <div className="h-4 w-px bg-[#D6D2C8] mx-1 hidden sm:block" />

        {/* Fault injection buttons */}
        <button
          onClick={handleSimulateDisconnect}
          className="px-2 py-1 bg-[#ECE9E0] hover:bg-[#FF4D4D] hover:text-[#FFFFFF] text-[#5E5E5E] border border-[#D6D2C8] rounded-sm text-[10px] font-semibold transition flex items-center gap-1"
          title="Inject CAM-03 stream failure"
        >
          <Unplug className="w-2.5 h-2.5" />
          <span>DISCONNECT CAM-03</span>
        </button>

        <button
          onClick={handleRestoreCam3}
          className="px-2 py-1 bg-[#ECE9E0] hover:bg-[#171717] hover:text-[#C7FF3D] text-[#5E5E5E] border border-[#D6D2C8] rounded-sm text-[10px] font-semibold transition flex items-center gap-1"
          title="Restore CAM-03 stream"
        >
          <CheckCircle2 className="w-2.5 h-2.5" />
          <span>RESTORE CAM-03</span>
        </button>

        <button
          onClick={handleResetDemo}
          className="px-2 py-1 bg-[#ECE9E0] hover:bg-[#171717] hover:text-[#F4F1E8] text-[#5E5E5E] border border-[#D6D2C8] rounded-sm text-[10px] font-semibold transition flex items-center gap-1"
          title="Reset Simulation State"
        >
          <RotateCcw className="w-2.5 h-2.5" />
          <span>RESET</span>
        </button>
      </div>
    </div>
  );
};
