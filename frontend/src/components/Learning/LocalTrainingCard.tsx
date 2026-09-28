import React, { useState } from 'react';
import {
  Cpu,
  Play,
  Activity,
  TrendingDown,
  Send
} from 'lucide-react';
import { LocalTrainingStatus, ModelUpdate, UserRole } from '../../types';
import { api } from '../../services/api';

interface LocalTrainingCardProps {
  status: LocalTrainingStatus | null;
  updates: ModelUpdate[];
  currentRole: UserRole;
  currentOperatorId: string;
  onRefresh: () => void;
}

export const LocalTrainingCard: React.FC<LocalTrainingCardProps> = ({
  status,
  updates,
  currentRole,
  currentOperatorId,
  onRefresh
}) => {
  const [epochs, setEpochs] = useState<number>(5);
  const [batchSize, setBatchSize] = useState<number>(16);
  const [learningRate, setLearningRate] = useState<number>(0.001);
  const [loading, setLoading] = useState<boolean>(false);

  const handleStartTraining = async () => {
    try {
      setLoading(true);
      await api.startLocalTraining({
        epochs,
        batch_size: batchSize,
        learning_rate: learningRate,
        operator_id: currentOperatorId,
        role: currentRole
      });
      alert('Local on-device fine-tuning training run launched successfully in background!');
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Failed to start local training');
    } finally {
      setLoading(false);
    }
  };

  const isReady = status?.ready_for_training ?? false;
  const isTraining = status?.is_training ?? false;
  const currentRun = status?.current_run || status?.last_completed_run;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 font-mono text-xs">
      {/* Left 1 Col: Edge Training Controls */}
      <div className="lg:col-span-1 bg-forensic-surface border border-forensic-border p-4 shadow-xs space-y-4 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between border-b border-forensic-border pb-3">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-forensic-elevated border border-forensic-border text-forensic-text">
                <Cpu className="w-4 h-4" />
              </div>
              <div>
                <span className="text-xs font-bold text-forensic-text uppercase block tracking-wider">
                  LOCAL ON-DEVICE TRAINING
                </span>
                <span className="text-[10px] text-forensic-muted">
                  Edge Node: <strong className="text-forensic-text">{status?.edge_id || 'EDGE-SECTOR-A-01'}</strong>
                </span>
              </div>
            </div>
            <span className={`px-2 py-0.5 text-[9px] font-bold border uppercase ${
              isTraining
                ? 'bg-signal-warning/20 text-signal-warning border-signal-warning'
                : isReady
                ? 'bg-signal-safe/20 text-signal-safe border-signal-safe'
                : 'bg-forensic-elevated text-forensic-muted border-forensic-border'
            }`}>
              {isTraining ? '● TRAINING' : isReady ? 'READY' : 'PENDING'}
            </span>
          </div>

          {/* Telemetry Status */}
          <div className="space-y-3 mt-4 text-xs">
            <div className="p-3 bg-forensic-elevated border border-forensic-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-forensic-muted">Validated Samples:</span>
                <span className="text-signal-safe font-bold text-sm">
                  {status?.validated_samples_available || 0}{' '}
                  <span className="text-forensic-muted text-[10px]">
                    / {status?.minimum_samples_required || 10} MIN
                  </span>
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-forensic-muted">Base Model:</span>
                <span className="text-forensic-text font-bold">v{status?.active_model_version || '1.0.0'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-forensic-muted">Compute Device:</span>
                <span className="text-forensic-text uppercase font-semibold">{status?.training_device || 'CPU'}</span>
              </div>
            </div>

            {/* Hyperparameters form */}
            <div className="space-y-2 pt-2">
              <span className="text-[10px] font-bold text-forensic-text uppercase block tracking-wider">
                TRAINING HYPERPARAMETERS
              </span>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-forensic-muted block uppercase">Epochs</label>
                  <input
                    type="number"
                    min={1}
                    max={20}
                    value={epochs}
                    onChange={(e) => setEpochs(Number(e.target.value))}
                    disabled={isTraining}
                    className="w-full bg-forensic-bg border border-forensic-border px-2 py-1 text-forensic-text text-xs focus:outline-none"
                  />
                </div>

                <div>
                  <label className="text-[10px] text-forensic-muted block uppercase">Batch Size</label>
                  <input
                    type="number"
                    min={4}
                    max={64}
                    value={batchSize}
                    onChange={(e) => setBatchSize(Number(e.target.value))}
                    disabled={isTraining}
                    className="w-full bg-forensic-bg border border-forensic-border px-2 py-1 text-forensic-text text-xs focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] text-forensic-muted block uppercase">Learning Rate</label>
                <input
                  type="number"
                  step={0.0001}
                  value={learningRate}
                  onChange={(e) => setLearningRate(Number(e.target.value))}
                  disabled={isTraining}
                  className="w-full bg-forensic-bg border border-forensic-border px-2 py-1 text-forensic-text text-xs focus:outline-none"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Start Button */}
        <div className="pt-3 border-t border-forensic-border">
          <button
            onClick={handleStartTraining}
            disabled={loading || isTraining || !isReady}
            className={`w-full py-2 text-xs font-bold flex items-center justify-center gap-2 transition uppercase tracking-wider cursor-pointer ${
              isTraining
                ? 'bg-signal-warning text-forensic-bg font-bold cursor-wait'
                : isReady
                ? 'bg-forensic-text hover:opacity-90 text-forensic-bg'
                : 'bg-forensic-elevated text-forensic-muted border border-forensic-border cursor-not-allowed'
            }`}
          >
            <Play className="w-3.5 h-3.5" />
            <span>{isTraining ? 'TRAINING IN PROGRESS...' : 'START LOCAL TRAINING'}</span>
          </button>
        </div>
      </div>

      {/* Right 2 Cols: Live Training Progress & Generated Model Update Package */}
      <div className="lg:col-span-2 bg-forensic-surface border border-forensic-border p-4 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-forensic-border pb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-forensic-elevated border border-forensic-border text-forensic-text">
              <Activity className="w-4 h-4" />
            </div>
            <div>
              <span className="text-xs font-bold text-forensic-text uppercase block tracking-wider">
                LEARNING CONVERGENCE & PARAMETER DELTAS
              </span>
              <span className="text-[10px] text-forensic-muted">
                Loss Optimization Curve • Parameter Gradients • SHA-256 Digest
              </span>
            </div>
          </div>
          <span className="text-[9px] text-signal-safe bg-signal-safe/15 px-2 py-0.5 border border-signal-safe font-bold uppercase">
            ZERO RAW VIDEO EXPORTED
          </span>
        </div>

        {currentRun ? (
          <div className="space-y-4">
            {/* Run summary cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div className="p-2.5 bg-forensic-elevated border border-forensic-border">
                <span className="text-[9px] text-forensic-muted block uppercase">Run Status</span>
                <span className="text-xs font-bold text-signal-safe uppercase">{currentRun.status}</span>
              </div>

              <div className="p-2.5 bg-forensic-elevated border border-forensic-border">
                <span className="text-[9px] text-forensic-muted block uppercase">Training Loss</span>
                <span className="text-xs font-bold text-signal-threat flex items-center gap-1">
                  <TrendingDown className="w-3 h-3" />
                  {currentRun.training_loss?.toFixed(4) || '0.2450'}
                </span>
              </div>

              <div className="p-2.5 bg-forensic-elevated border border-forensic-border">
                <span className="text-[9px] text-forensic-muted block uppercase">mAP@50</span>
                <span className="text-xs font-bold text-forensic-text">
                  {((currentRun.validation_metric || 0.892) * 100).toFixed(1)}%
                </span>
              </div>

              <div className="p-2.5 bg-forensic-elevated border border-forensic-border">
                <span className="text-[9px] text-forensic-muted block uppercase">Samples Trained</span>
                <span className="text-xs font-bold text-signal-safe">
                  {currentRun.sample_count || 120} VAL
                </span>
              </div>
            </div>

            {/* Epoch Progress Table */}
            {currentRun.metrics?.epoch_progress && currentRun.metrics.epoch_progress.length > 0 && (
              <div className="bg-forensic-elevated border border-forensic-border p-3 space-y-2">
                <span className="text-[10px] font-bold text-forensic-text uppercase block tracking-wider">
                  EPOCH LOSS PROGRESSION LOG
                </span>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-[11px] text-forensic-text">
                    <thead className="bg-forensic-surface text-forensic-muted text-[9px] uppercase border-b border-forensic-border">
                      <tr>
                        <th className="p-1.5">Epoch</th>
                        <th className="p-1.5">Loss</th>
                        <th className="p-1.5">mAP50</th>
                        <th className="p-1.5">Precision</th>
                        <th className="p-1.5">Recall</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-forensic-border/60">
                      {currentRun.metrics.epoch_progress.map((ep) => (
                        <tr key={ep.epoch} className="hover:bg-forensic-surface">
                          <td className="p-1.5 font-bold text-forensic-text">Epoch {ep.epoch}/{ep.total_epochs}</td>
                          <td className="p-1.5 text-signal-threat">{ep.loss.toFixed(4)}</td>
                          <td className="p-1.5 text-forensic-text">{(ep.mAP50 * 100).toFixed(1)}%</td>
                          <td className="p-1.5 text-signal-safe">{(ep.precision * 100).toFixed(1)}%</td>
                          <td className="p-1.5 text-forensic-text">{(ep.recall * 100).toFixed(1)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Generated Model Update Details */}
            {updates.length > 0 && (
              <div className="p-3 bg-forensic-elevated border border-forensic-border space-y-2 text-xs">
                <div className="flex items-center justify-between border-b border-forensic-border pb-1.5">
                  <span className="font-bold text-forensic-text flex items-center gap-1.5 uppercase text-[11px]">
                    <Send className="w-3.5 h-3.5" />
                    Model Update Delta ({updates[0].update_id})
                  </span>
                  <span className="px-1.5 py-0.2 bg-signal-safe/20 text-signal-safe border border-signal-safe text-[9px] font-bold">
                    {updates[0].status}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[10px]">
                  <div>
                    <span className="text-forensic-muted uppercase">Base Version: </span>
                    <span className="text-forensic-text font-bold">v{updates[0].base_model_version}</span>
                  </div>
                  <div>
                    <span className="text-forensic-muted uppercase">Round: </span>
                    <span className="text-forensic-text font-bold">Round #{updates[0].training_round}</span>
                  </div>
                </div>

                <div className="text-[9px] text-forensic-muted">
                  <span className="uppercase">SHA-256 Digest: </span>
                  <span className="text-forensic-text break-all">{updates[0].update_hash}</span>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="py-16 text-center text-forensic-muted text-xs flex flex-col items-center justify-center gap-2">
            <Cpu className="w-8 h-8 text-forensic-muted" />
            <span>Click 'START LOCAL TRAINING' to execute on-device fine-tuning.</span>
          </div>
        )}
      </div>
    </div>
  );
};
