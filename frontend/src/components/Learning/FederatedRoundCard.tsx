import React, { useState } from 'react';
import {
  Server,
  Plus,
  CheckCircle2,
  Sparkles,
  Shield,
} from 'lucide-react';
import { FederatedRound, UserRole } from '../../types';
import { api } from '../../services/api';

interface FederatedRoundCardProps {
  rounds: FederatedRound[];
  activeVersion: string;
  currentRole: UserRole;
  currentOperatorId: string;
  onRefresh: () => void;
}

export const FederatedRoundCard: React.FC<FederatedRoundCardProps> = ({
  rounds,
  activeVersion,
  currentRole,
  currentOperatorId: _currentOperatorId,
  onRefresh
}) => {
  const [selectedRound, setSelectedRound] = useState<FederatedRound | null>(
    rounds.length > 0 ? rounds[0] : null
  );
  const [loading, setLoading] = useState<boolean>(false);

  const handleCreateRound = async () => {
    try {
      setLoading(true);
      await api.createFederatedRound(activeVersion, ['EDGE-SECTOR-A-01', 'EDGE-SECTOR-A-02', 'EDGE-SECTOR-B-01']);
      alert('New federated aggregation round opened!');
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Failed to create round');
    } finally {
      setLoading(false);
    }
  };

  const handleAggregate = async (roundId: string) => {
    try {
      setLoading(true);
      const res = await api.aggregateFederatedRound(roundId);
      alert(`Federated Aggregation successful! Candidate model v${res.candidate_version} created in registry.`);
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Failed to aggregate round');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 font-mono text-xs">
      {/* Left 1 Col: Rounds Queue & Initiation */}
      <div className="lg:col-span-1 bg-forensic-surface border border-forensic-border p-4 shadow-xs space-y-4 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between border-b border-forensic-border pb-3">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-forensic-elevated border border-forensic-border text-forensic-text">
                <Server className="w-4 h-4" />
              </div>
              <div>
                <span className="text-xs font-bold text-forensic-text uppercase block tracking-wider">
                  FEDERATED ROUNDS
                </span>
                <span className="text-[10px] text-forensic-muted">
                  Weighted FedAvg Engine
                </span>
              </div>
            </div>
            <button
              onClick={handleCreateRound}
              disabled={loading || currentRole === 'OPERATOR'}
              className="px-2 py-1 bg-forensic-text text-forensic-bg hover:opacity-90 text-[10px] font-bold transition flex items-center gap-1 disabled:opacity-40 cursor-pointer uppercase"
              title="Initiate next federated round"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>New Round</span>
            </button>
          </div>

          {/* Rounds list */}
          <div className="space-y-2 mt-4 max-h-[450px] overflow-y-auto pr-1">
            {rounds.map((r) => {
              const isSelected = selectedRound?.round_id === r.round_id;
              return (
                <div
                  key={r.round_id}
                  onClick={() => setSelectedRound(r)}
                  className={`p-3 border transition cursor-pointer flex flex-col gap-1.5 ${
                    isSelected
                      ? 'bg-forensic-elevated border-forensic-text'
                      : 'bg-forensic-bg border-forensic-border hover:border-forensic-muted'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-forensic-text uppercase">{r.round_id}</span>
                    <span className={`px-1.5 py-0.2 text-[9px] font-bold border uppercase ${
                      r.status === 'COMPLETED'
                        ? 'bg-signal-safe/20 text-signal-safe border-signal-safe'
                        : r.status === 'COLLECTING'
                        ? 'bg-forensic-surface text-forensic-text border-forensic-border'
                        : 'bg-signal-warning/20 text-signal-warning border-signal-warning'
                    }`}>
                      {r.status}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-forensic-muted">
                    <span>Base: v{r.base_model_version}</span>
                    <span>{new Date(r.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Right 2 Cols: Active Round Participant Inspection & FedAvg Trigger */}
      <div className="lg:col-span-2 bg-forensic-surface border border-forensic-border p-4 shadow-xs space-y-4 flex flex-col justify-between">
        {selectedRound ? (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-forensic-border pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-forensic-text uppercase tracking-wider">{selectedRound.round_id}</span>
                  <span className="px-1.5 py-0.2 bg-forensic-elevated text-forensic-text border border-forensic-border text-[10px] font-bold uppercase">
                    Method: {selectedRound.aggregation_method}
                  </span>
                </div>
                <span className="text-[10px] text-forensic-muted">
                  Base Model: <strong className="text-forensic-text">v{selectedRound.base_model_version}</strong> • Created: {new Date(selectedRound.created_at).toLocaleString()}
                </span>
              </div>

              {selectedRound.status !== 'COMPLETED' && (
                <button
                  onClick={() => handleAggregate(selectedRound.round_id)}
                  disabled={loading || currentRole === 'OPERATOR'}
                  className="px-3 py-1.5 bg-forensic-text hover:opacity-90 text-forensic-bg text-[10px] font-bold transition flex items-center gap-1.5 uppercase disabled:opacity-40 cursor-pointer"
                  title="Combine edge parameter updates via FedAvg"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>AGGREGATE WITH FEDAVG</span>
                </button>
              )}
            </div>

            {/* Participating Edge Outposts */}
            <div className="space-y-2">
              <span className="text-[10px] font-bold text-forensic-text uppercase flex items-center gap-1.5 tracking-wider">
                <Shield className="w-3.5 h-3.5 text-forensic-text" />
                Participating Edge Outposts ({selectedRound.participants?.length || 3})
              </span>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                {(selectedRound.participants || ['EDGE-SECTOR-A-01', 'EDGE-SECTOR-A-02', 'EDGE-SECTOR-B-01']).map((edgeId, idx) => (
                  <div key={edgeId} className="p-2.5 bg-forensic-elevated border border-forensic-border flex flex-col justify-between gap-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-forensic-text text-[11px]">{edgeId}</span>
                      <CheckCircle2 className="w-3.5 h-3.5 text-signal-safe" />
                    </div>
                    <div className="text-[10px] text-forensic-muted">
                      <span>Status: </span>
                      <span className="text-signal-safe font-bold">READY ✓</span>
                    </div>
                    <div className="text-[10px] text-forensic-muted">
                      <span>Samples: </span>
                      <span className="text-forensic-text font-bold">{85 + (idx * 15)} validated</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Mathematical FedAvg Explanation Card */}
            <div className="p-3 bg-forensic-elevated border border-forensic-border space-y-2 text-xs">
              <span className="font-bold text-forensic-text uppercase text-[10px] tracking-wider block">
                Weighted Federated Averaging Formula:
              </span>
              <div className="p-2 bg-forensic-surface border border-forensic-border text-forensic-text text-[11px]">
                <code>ΔW_global = Σ [ (N_k / N_total) * ΔW_k ]</code>
              </div>
              <p className="text-[10px] text-forensic-muted leading-relaxed">
                Aggregates parameter gradient norms from all participating outposts weighted by validated sample counts. Produces candidate model without exporting raw surveillance footage.
              </p>
            </div>
          </div>
        ) : (
          <div className="py-16 text-center text-forensic-muted text-xs flex flex-col items-center justify-center gap-2">
            <Server className="w-8 h-8 text-forensic-muted" />
            <span>Select a federated round to inspect.</span>
          </div>
        )}
      </div>
    </div>
  );
};
