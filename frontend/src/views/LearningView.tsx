import React, { useState, useEffect, useCallback } from 'react';
import {
  UserRole,
  ModelVersion,
  LocalTrainingStatus,
  ModelUpdate,
  FederatedRound,
  TrainingSample,
  PrivacyStatus,
} from '../types';
import { api } from '../services/api';
import { PrivacyStatusBanner } from '../components/Learning/PrivacyStatusBanner';
import { ModelRegistryCard } from '../components/Learning/ModelRegistryCard';
import { LocalTrainingCard } from '../components/Learning/LocalTrainingCard';
import { FederatedRoundCard } from '../components/Learning/FederatedRoundCard';
import { SampleReviewTable } from '../components/Learning/SampleReviewTable';
import {
  Cpu,
  Layers,
  Sparkles,
  Database,
  Network,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Flame,
} from 'lucide-react';

interface LearningViewProps {
  currentRole: UserRole;
  currentOperatorId: string;
}

type TabType = 'OVERVIEW' | 'REGISTRY' | 'LOCAL' | 'FEDERATED' | 'SAMPLES';

export const LearningView: React.FC<LearningViewProps> = ({
  currentRole,
  currentOperatorId,
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('OVERVIEW');
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);
  const [demoRunning, setDemoRunning] = useState<boolean>(false);
  const [demoSuccess, setDemoSuccess] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Loaded State for child components
  const [activeModel, setActiveModel] = useState<ModelVersion | null>(null);
  const [candidateModels, setCandidateModels] = useState<ModelVersion[]>([]);
  const [allModels, setAllModels] = useState<ModelVersion[]>([]);
  const [trainingStatus, setTrainingStatus] = useState<LocalTrainingStatus | null>(null);
  const [updates, setUpdates] = useState<ModelUpdate[]>([]);
  const [rounds, setRounds] = useState<FederatedRound[]>([]);
  const [samples, setSamples] = useState<TrainingSample[]>([]);
  const [privacyStatus, setPrivacyStatus] = useState<PrivacyStatus | null>(null);

  const fetchLearningData = useCallback(async () => {
    try {
      setIsLoading(true);
      const [
        activeMod,
        candMods,
        allMods,
        trainStat,
        fRounds,
        tSamples,
        privStat,
      ] = await Promise.all([
        api.getActiveModel().catch(() => null),
        api.getCandidateModels().catch(() => []),
        api.getModels().catch(() => []),
        api.getTrainingStatus().catch(() => null),
        api.getFederatedRounds().catch(() => []),
        api.getTrainingSamples(undefined, 100).catch(() => []),
        api.getPrivacyStatus().catch(() => null),
      ]);

      setActiveModel(activeMod);
      setCandidateModels(candMods);
      setAllModels(allMods);
      setTrainingStatus(trainStat);
      setRounds(fRounds);
      setSamples(tSamples);
      setPrivacyStatus(privStat);
    } catch (err: any) {
      console.error('Error fetching learning state:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLearningData();
  }, [fetchLearningData, refreshTrigger]);

  const handleRefresh = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  const handleRunHeroDemo = async () => {
    try {
      setDemoRunning(true);
      setErrorMsg(null);
      setDemoSuccess(null);
      const res = await api.runPhase9Demo();
      setDemoSuccess(
        `Phase 9 E2E Demo executed successfully! Candidate: ${res.candidate_model_id} | Accuracy: +${(res.accuracy_improvement * 100).toFixed(1)}% | Privacy: ${res.privacy_guarantee}`
      );
      handleRefresh();
    } catch (e: any) {
      console.error('Error running Phase 9 demo:', e);
      setErrorMsg(e.message || 'Failed to execute Phase 9 learning demonstration');
    } finally {
      setDemoRunning(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 font-sans">
      {/* Header Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-forensic-surface p-4 border border-forensic-border shadow-xs">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-forensic-elevated border border-forensic-border text-forensic-text">
            <Cpu className="w-5 h-5 text-forensic-text" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xs font-mono font-bold tracking-widest text-forensic-text uppercase">
                ON-DEVICE & FEDERATED LEARNING HUB
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-mono font-bold bg-forensic-elevated text-forensic-text border border-forensic-border">
                PHASE 09 // LEARN
              </span>
            </div>
            <p className="text-[11px] font-mono text-forensic-muted mt-0.5">
              Privacy-preserving edge fine-tuning, zero raw video transmission, FedAvg parameter aggregation, and controlled candidate model governance.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRunHeroDemo}
            disabled={demoRunning}
            className="flex items-center gap-2 px-3 py-1.5 bg-forensic-text text-forensic-bg hover:opacity-90 disabled:opacity-50 font-mono text-[11px] font-bold tracking-wider uppercase transition-all cursor-pointer"
          >
            {demoRunning ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Flame className="w-3.5 h-3.5 text-signal-warning" />
            )}
            <span>{demoRunning ? 'PIPELINE RUNNING...' : 'RUN PHASE 9 E2E DEMO'}</span>
          </button>

          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="px-3 py-1.5 bg-forensic-elevated hover:bg-forensic-border text-forensic-text border border-forensic-border text-[11px] font-mono font-bold flex items-center gap-1.5 transition-colors cursor-pointer"
            title="Refresh Learning State"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>SYNC</span>
          </button>
        </div>
      </div>

      {/* Notification Banners */}
      {demoSuccess && (
        <div className="p-3 bg-signal-safe/10 border border-signal-safe text-forensic-text text-xs font-mono flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-signal-safe flex-shrink-0" />
            <span>{demoSuccess}</span>
          </div>
          <button
            onClick={() => setDemoSuccess(null)}
            className="text-forensic-muted hover:text-forensic-text text-[10px] uppercase font-mono px-2 py-0.5 bg-forensic-surface border border-forensic-border cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {errorMsg && (
        <div className="p-3 bg-signal-threat/10 border border-signal-threat text-signal-threat text-xs font-mono flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <AlertTriangle className="w-4 h-4 text-signal-threat flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button
            onClick={() => setErrorMsg(null)}
            className="text-forensic-muted hover:text-forensic-text text-[10px] uppercase font-mono px-2 py-0.5 bg-forensic-surface border border-forensic-border cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Privacy Audit Telemetry Banner */}
      <PrivacyStatusBanner status={privacyStatus} />

      {/* Navigation Tabs */}
      <div className="flex items-center gap-1 border-b border-forensic-border pb-1 overflow-x-auto">
        {[
          { id: 'OVERVIEW', label: '01 ALL MODULES', icon: Layers },
          { id: 'REGISTRY', label: '02 GOVERNANCE & BENCHMARK', icon: Sparkles },
          { id: 'LOCAL', label: '03 EDGE FINE-TUNING', icon: Cpu },
          { id: 'FEDERATED', label: '04 FEDERATED AGGREGATOR', icon: Network },
          { id: 'SAMPLES', label: '05 SAMPLE TRIAGE & VALIDATION', icon: Database },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabType)}
              className={`flex items-center gap-2 px-3 py-1.5 text-[11px] font-mono tracking-wider font-bold transition-all cursor-pointer ${
                isActive
                  ? 'bg-forensic-text text-forensic-bg border border-forensic-text'
                  : 'text-forensic-muted hover:text-forensic-text bg-forensic-surface hover:bg-forensic-elevated border border-forensic-border'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Panels */}
      {activeTab === 'OVERVIEW' && (
        <div className="space-y-6">
          <ModelRegistryCard
            activeModel={activeModel}
            candidateModels={candidateModels}
            allModels={allModels}
            currentRole={currentRole}
            currentOperatorId={currentOperatorId}
            onRefresh={handleRefresh}
          />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <LocalTrainingCard
              status={trainingStatus}
              updates={updates}
              currentRole={currentRole}
              currentOperatorId={currentOperatorId}
              onRefresh={handleRefresh}
            />
            <FederatedRoundCard
              rounds={rounds}
              activeVersion={activeModel?.version || '1.0.0'}
              currentRole={currentRole}
              currentOperatorId={currentOperatorId}
              onRefresh={handleRefresh}
            />
          </div>

          <SampleReviewTable
            samples={samples}
            currentRole={currentRole}
            currentOperatorId={currentOperatorId}
            onRefresh={handleRefresh}
          />
        </div>
      )}

      {activeTab === 'REGISTRY' && (
        <ModelRegistryCard
          activeModel={activeModel}
          candidateModels={candidateModels}
          allModels={allModels}
          currentRole={currentRole}
          currentOperatorId={currentOperatorId}
          onRefresh={handleRefresh}
        />
      )}

      {activeTab === 'LOCAL' && (
        <LocalTrainingCard
          status={trainingStatus}
          updates={updates}
          currentRole={currentRole}
          currentOperatorId={currentOperatorId}
          onRefresh={handleRefresh}
        />
      )}

      {activeTab === 'FEDERATED' && (
        <FederatedRoundCard
          rounds={rounds}
          activeVersion={activeModel?.version || '1.0.0'}
          currentRole={currentRole}
          currentOperatorId={currentOperatorId}
          onRefresh={handleRefresh}
        />
      )}

      {activeTab === 'SAMPLES' && (
        <SampleReviewTable
          samples={samples}
          currentRole={currentRole}
          currentOperatorId={currentOperatorId}
          onRefresh={handleRefresh}
        />
      )}
    </div>
  );
};
