import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import {
  Sparkles,
  Play,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Flame,
  Shield,
  Sun,
  Moon,
  Compass,
  Car,
  XCircle,
  Terminal,
  Cpu,
  Lock,
  Wifi,
  WifiOff,
  ArrowRight,
  Eye,
  Activity,
} from 'lucide-react';

interface SimulationLabViewProps {
  onRefresh: () => void;
  onSelectSubject?: (subjectId: string) => void;
  onSelectIncident?: (incidentId: string) => void;
}

export const SimulationLabView: React.FC<SimulationLabViewProps> = ({
  onRefresh,
}) => {
  const [runningScenario, setRunningScenario] = useState<number | string | null>(null);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [demoStatus, setDemoStatus] = useState<any>(null);
  const [executionLogs, setExecutionLogs] = useState<
    { id: string; timestamp: string; title: string; result: any; status: 'SUCCESS' | 'ERROR' }[]
  >([]);

  const fetchStatus = async () => {
    try {
      const data = await api.getDemoStatus();
      setDemoStatus(data);
    } catch {
      // Offline fallback
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const demoSteps = [
    { key: '1', label: '1. SEE', title: 'CCTV Matrix & Streams', icon: Eye },
    { key: '2', label: '2. UNDERSTAND', title: 'ByteTrack Detection', icon: Activity },
    { key: '3', label: '3. VERIFY', title: 'Virtual Fence Gate', icon: Shield },
    { key: '4', label: '4. SUPPRESS', title: 'False-Positive Filter', icon: XCircle },
    { key: '5', label: '5. CORRELATE', title: 'Cross-Camera Graph', icon: Compass },
    { key: '6', label: '6. ASSESS', title: 'Explainable Risk Scoring', icon: Flame },
    { key: '7', label: '7. RESPOND', title: 'SOC Operator Triage', icon: Shield },
    { key: '8', label: '8. PROVE', title: 'SHA-256 Ledger Anchor', icon: Lock },
    { key: '9', label: '9. TAMPER', title: 'Tamper Detection', icon: AlertTriangle },
    { key: '10', label: '10. RESTORE', title: 'Cryptographic Restore', icon: CheckCircle2 },
    { key: '11', label: '11. OFFLINE', title: 'Edge Autonomous Buffer', icon: WifiOff },
    { key: '12', label: '12. SYNC', title: 'Queue Synchronization', icon: Wifi },
    { key: '13', label: '13. LEARN', title: 'Federated Fine-Tuning', icon: Cpu },
  ];

  const runHeroDemo = async () => {
    try {
      setRunningScenario('hero');
      const res = await api.runHeroDemo();
      const newLog = {
        id: `HERO-${Date.now()}`,
        timestamp: new Date().toLocaleTimeString(),
        title: 'Master Hero Demonstration (34-Step Architecture Run)',
        result: res,
        status: 'SUCCESS' as const,
      };
      setExecutionLogs((prev) => [newLog, ...prev]);
      fetchStatus();
      onRefresh();
    } catch (e: any) {
      const errLog = {
        id: `ERR-${Date.now()}`,
        timestamp: new Date().toLocaleTimeString(),
        title: 'Hero Scenario Execution Failed',
        result: { error: e.message || 'Error executing hero demo' },
        status: 'ERROR' as const,
      };
      setExecutionLogs((prev) => [errLog, ...prev]);
    } finally {
      setRunningScenario(null);
    }
  };

  const executeSpecificStep = async (stepKey: string, stepTitle: string) => {
    try {
      setRunningScenario(`step-${stepKey}`);
      const res = await api.executeDemoStep(stepKey);
      const newLog = {
        id: `STEP-${stepKey}-${Date.now()}`,
        timestamp: new Date().toLocaleTimeString(),
        title: `Executed Demo Step ${stepKey}: ${stepTitle}`,
        result: res,
        status: 'SUCCESS' as const,
      };
      setExecutionLogs((prev) => [newLog, ...prev]);
      const idx = demoSteps.findIndex((s) => s.key === stepKey);
      if (idx !== -1) setCurrentStepIndex(idx);
      fetchStatus();
      onRefresh();
    } catch (e: any) {
      const errLog = {
        id: `ERR-${Date.now()}`,
        timestamp: new Date().toLocaleTimeString(),
        title: `Failed to execute Step ${stepKey}`,
        result: { error: e.message || 'Step execution error' },
        status: 'ERROR' as const,
      };
      setExecutionLogs((prev) => [errLog, ...prev]);
    } finally {
      setRunningScenario(null);
    }
  };

  const handleNextStep = () => {
    const nextIdx = (currentStepIndex + 1) % demoSteps.length;
    const step = demoSteps[nextIdx];
    executeSpecificStep(step.key, step.title);
  };

  const runScenario = async (scenarioNum: number, name: string) => {
    try {
      setRunningScenario(scenarioNum);
      const res = await api.runScenario(scenarioNum);
      const newLog = {
        id: `LOG-${Date.now()}`,
        timestamp: new Date().toLocaleTimeString(),
        title: `Executed ${name}`,
        result: res,
        status: 'SUCCESS' as const,
      };
      setExecutionLogs((prev) => [newLog, ...prev]);
      fetchStatus();
      onRefresh();
    } catch (e: any) {
      const errLog = {
        id: `ERR-${Date.now()}`,
        timestamp: new Date().toLocaleTimeString(),
        title: `Failed to execute ${name}`,
        result: { error: e.message || 'Execution error' },
        status: 'ERROR' as const,
      };
      setExecutionLogs((prev) => [errLog, ...prev]);
    } finally {
      setRunningScenario(null);
    }
  };

  const handleReset = async () => {
    try {
      setRunningScenario('reset');
      await api.resetDemoState();
      setCurrentStepIndex(0);
      const newLog = {
        id: `RESET-${Date.now()}`,
        timestamp: new Date().toLocaleTimeString(),
        title: 'Reset All Demo State',
        result: { message: 'Reset cross-camera subjects, incidents, risk assessments, ledger blocks, sync queue, and model candidates.' },
        status: 'SUCCESS' as const,
      };
      setExecutionLogs((prev) => [newLog, ...prev]);
      fetchStatus();
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Failed to reset state');
    } finally {
      setRunningScenario(null);
    }
  };

  const scenarios = [
    {
      num: 1,
      title: '01 / NORMAL MOVEMENT',
      risk: 'LOW (15 PTS)',
      icon: Sun,
      desc: 'Daylight movement outside restricted polygons. AI classifies normal activity without generating alarm.',
    },
    {
      num: 2,
      title: '02 / VERIFIED ZONE ENTRY',
      risk: 'MEDIUM (45 PTS)',
      icon: Shield,
      desc: 'Target crosses into Virtual Fence polygon and passes 3-frame verification gate.',
    },
    {
      num: 3,
      title: '03 / NIGHT INTRUSION',
      risk: 'HIGH (75 PTS)',
      icon: Moon,
      desc: 'Restricted zone breach during night time hours + virtual fence crossing. High priority security alert.',
    },
    {
      num: 4,
      title: '04 / MULTI-CAMERA JOURNEY',
      risk: 'CAM-01 → 02 → 03',
      icon: Compass,
      desc: 'Simulates a deterministic transit across 3 cameras with appearance Re-ID and topology validation.',
    },
    {
      num: 5,
      title: '05 / PERSON + VEHICLE LINK',
      risk: 'CORRELATED',
      icon: Car,
      desc: 'Correlates Person P183 with Vehicle V22 in spatial proximity without pre-judging intent.',
    },
    {
      num: 6,
      title: '06 / MULTI-FACTOR COMPOSITE',
      risk: 'CRITICAL (95 PTS)',
      icon: Flame,
      desc: 'Full threat profile hitting restricted zone, fence crossing, night movement, and vehicle factors.',
    },
  ];

  return (
    <div className="space-y-4 font-sans font-mono">
      {/* Header Toolbar */}
      <div className="bg-[#ECE9E0] border border-[#D6D2C8] rounded-sm p-3.5 shadow-none flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-[#171717]" />
            <div>
              <h2 className="text-xs font-bold text-[#171717] uppercase tracking-wider">
                DETERMINISTIC SIMULATION & JURY PRESENTATION LAB
              </h2>
              <p className="text-[10px] text-[#5E5E5E]">
                13-STAGE STATE MACHINE CONTROLLER • MASTER HERO SCENARIO • ZERO-RISK RESET
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={runHeroDemo}
            disabled={runningScenario !== null}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#171717] hover:bg-[#292929] text-[#F4F1E8] rounded-sm font-bold transition disabled:opacity-50"
          >
            <Play className="w-3 h-3 text-[#C7FF3D]" />
            <span>{runningScenario === 'hero' ? 'EXECUTING HERO DEMO...' : 'RUN MASTER HERO DEMO'}</span>
          </button>

          <button
            onClick={handleReset}
            disabled={runningScenario !== null}
            className="flex items-center gap-1.5 px-2.5 py-1.5 bg-[#FFFFFF] hover:bg-[#F4F1E8] text-[#171717] border border-[#D6D2C8] rounded-sm font-bold transition"
          >
            <RotateCcw className="w-3 h-3 text-[#FF4D4D]" />
            <span>RESET ALL STATE</span>
          </button>
        </div>
      </div>

      {/* 13 Stage Pipeline */}
      <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-4 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#ECE9E0] pb-2">
          <div className="flex items-center gap-2">
            <Activity className="w-3.5 h-3.5 text-[#171717]" />
            <span className="text-xs font-bold text-[#171717] uppercase">
              INTERACTIVE DEMO STATE MACHINE (13 STAGES)
            </span>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="text-[10px] text-[#5E5E5E]">
              CURRENT: <strong className="text-[#171717]">{demoStatus?.current_stage || demoSteps[currentStepIndex].label}</strong>
            </span>
            <button
              onClick={handleNextStep}
              disabled={runningScenario !== null}
              className="px-2 py-0.5 bg-[#171717] hover:bg-[#292929] text-[#F4F1E8] rounded-sm text-[10px] font-bold flex items-center gap-1 transition"
            >
              <span>NEXT</span>
              <ArrowRight className="w-3 h-3 text-[#C7FF3D]" />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-1.5">
          {demoSteps.map((step, idx) => {
            const Icon = step.icon;
            const isCurrent = currentStepIndex === idx;

            return (
              <button
                key={step.key}
                onClick={() => executeSpecificStep(step.key, step.title)}
                disabled={runningScenario !== null}
                className={`p-2 rounded-sm border text-left transition flex flex-col justify-between gap-1 ${
                  isCurrent
                    ? 'bg-[#171717] border-[#171717] text-[#C7FF3D]'
                    : 'bg-[#F4F1E8] border-[#D6D2C8] text-[#171717] hover:border-[#171717]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <Icon className="w-3 h-3" />
                  <span className="text-[8px] opacity-70">#{step.key}</span>
                </div>
                <div>
                  <div className="text-[9px] font-bold truncate">{step.label}</div>
                  <div className="text-[8px] opacity-80 truncate">{step.title}</div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Scenario Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
        {scenarios.map((sc) => {
          const Icon = sc.icon;
          const isRunning = runningScenario === sc.num;

          return (
            <div
              key={sc.num}
              className="p-3.5 bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm flex flex-col justify-between gap-3"
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Icon className="w-4 h-4 text-[#171717]" />
                    <span className="font-bold text-xs text-[#171717]">
                      {sc.title}
                    </span>
                  </div>
                  <span className="text-[9px] font-bold px-1.5 py-0.2 rounded-sm bg-[#ECE9E0] text-[#171717] border border-[#D6D2C8]">
                    {sc.risk}
                  </span>
                </div>

                <p className="text-[10px] text-[#5E5E5E] leading-relaxed">
                  {sc.desc}
                </p>
              </div>

              <button
                onClick={() => runScenario(sc.num, sc.title)}
                disabled={runningScenario !== null}
                className="w-full py-1 bg-[#171717] hover:bg-[#292929] text-[#F4F1E8] rounded-sm text-xs font-bold flex items-center justify-center gap-1.5 transition disabled:opacity-50"
              >
                <Play className="w-3 h-3 text-[#C7FF3D]" />
                <span>{isRunning ? 'EXECUTING...' : 'TRIGGER SCENARIO'}</span>
              </button>
            </div>
          );
        })}

        {/* False Match Demo */}
        <div className="p-3.5 bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm flex flex-col justify-between gap-3">
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <XCircle className="w-4 h-4 text-[#FF4D4D]" />
                <span className="font-bold text-xs text-[#171717]">
                  05 / FALSE MATCH REJECTION
                </span>
              </div>
              <span className="text-[9px] font-bold px-1.5 py-0.2 rounded-sm bg-[#ECE9E0] text-[#171717] border border-[#D6D2C8]">
                SUPPRESSION
              </span>
            </div>

            <p className="text-[10px] text-[#5E5E5E] leading-relaxed">
              Demonstrates strict spatial rejection: an incompatible track outside the topology time window is rejected without creating a false link.
            </p>
          </div>

          <button
            onClick={() => executeSpecificStep('4', 'False Match Suppression')}
            disabled={runningScenario !== null}
            className="w-full py-1 bg-[#171717] hover:bg-[#292929] text-[#F4F1E8] rounded-sm text-xs font-bold flex items-center justify-center gap-1.5 transition disabled:opacity-50"
          >
            <Play className="w-3 h-3 text-[#C7FF3D]" />
            <span>TRIGGER REJECTION TEST</span>
          </button>
        </div>
      </div>

      {/* Execution Logs Console */}
      <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-3.5 space-y-2">
        <div className="flex items-center justify-between border-b border-[#ECE9E0] pb-2">
          <span className="text-xs font-bold text-[#171717] uppercase flex items-center gap-1.5">
            <Terminal className="w-3.5 h-3.5 text-[#171717]" />
            SIMULATION EXECUTION LOGS ({executionLogs.length} EVENTS)
          </span>
          <button
            onClick={() => setExecutionLogs([])}
            className="text-[10px] text-[#5E5E5E] hover:text-[#171717]"
          >
            [CLEAR CONSOLE]
          </button>
        </div>

        {executionLogs.length === 0 ? (
          <div className="p-6 text-center text-[#5E5E5E] text-xs">
            Trigger a scenario above to observe real-time execution outputs.
          </div>
        ) : (
          <div className="max-h-64 overflow-y-auto space-y-1.5 pr-1">
            {executionLogs.map((log) => (
              <div
                key={log.id}
                className="p-2.5 bg-[#F4F1E8] rounded-sm border border-[#D6D2C8] text-xs space-y-1"
              >
                <div className="flex items-center justify-between text-[10px]">
                  <span className={`font-bold ${log.status === 'SUCCESS' ? 'text-[#1A5319]' : 'text-[#C53030]'}`}>
                    {log.status === 'SUCCESS' ? '✓' : '✗'} {log.title}
                  </span>
                  <span className="text-[#5E5E5E]">{log.timestamp}</span>
                </div>
                <pre className="text-[10px] text-[#171717] bg-[#FFFFFF] p-2 rounded-sm border border-[#D6D2C8] overflow-x-auto">
                  {JSON.stringify(log.result, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
