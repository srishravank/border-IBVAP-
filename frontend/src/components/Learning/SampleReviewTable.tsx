import React, { useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  Edit3,
  Camera,
  Check,
  X,
  UserCheck
} from 'lucide-react';
import { TrainingSample, UserRole } from '../../types';
import { api } from '../../services/api';

interface SampleReviewTableProps {
  samples: TrainingSample[];
  currentRole: UserRole;
  currentOperatorId: string;
  onRefresh: () => void;
}

export const SampleReviewTable: React.FC<SampleReviewTableProps> = ({
  samples,
  currentRole,
  currentOperatorId,
  onRefresh
}) => {
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [editingSampleId, setEditingSampleId] = useState<string | null>(null);
  const [relabelValue, setRelabelValue] = useState<string>('person');
  const [loading, setLoading] = useState<boolean>(false);

  const filteredSamples = samples.filter((s) => {
    if (filterStatus !== 'ALL' && s.validation_status !== filterStatus) return false;
    return true;
  });

  const handleApprove = async (sampleId: string) => {
    try {
      setLoading(true);
      await api.approveTrainingSample(sampleId, currentOperatorId, currentRole);
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Failed to approve sample');
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async (sampleId: string) => {
    try {
      setLoading(true);
      await api.rejectTrainingSample(sampleId, currentOperatorId, currentRole);
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Failed to reject sample');
    } finally {
      setLoading(false);
    }
  };

  const handleRelabel = async (sampleId: string) => {
    if (!relabelValue) return;
    try {
      setLoading(true);
      await api.relabelTrainingSample(sampleId, relabelValue, currentOperatorId, currentRole);
      setEditingSampleId(null);
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Failed to relabel sample');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-forensic-surface border border-forensic-border p-4 shadow-xs space-y-4 font-mono text-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-forensic-border pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-forensic-elevated border border-forensic-border text-forensic-text">
            <UserCheck className="w-4 h-4" />
          </div>
          <div>
            <span className="text-xs font-bold text-forensic-text uppercase block tracking-wider">
              HUMAN-IN-THE-LOOP TRAINING SAMPLE TRIAGE ({filteredSamples.length})
            </span>
            <span className="text-[10px] text-forensic-muted">
              Only explicitly validated samples are eligible for on-device fine-tuning
            </span>
          </div>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1 bg-forensic-elevated p-1 border border-forensic-border text-xs">
          {['ALL', 'PENDING', 'VALIDATED', 'REJECTED'].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-2 py-0.5 transition text-[10px] font-bold uppercase cursor-pointer ${
                filterStatus === st
                  ? 'bg-forensic-text text-forensic-bg'
                  : 'text-forensic-muted hover:text-forensic-text'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Samples Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-forensic-text">
          <thead className="bg-forensic-elevated text-forensic-muted text-[9px] uppercase border-b border-forensic-border">
            <tr>
              <th className="p-2.5">Sample ID</th>
              <th className="p-2.5">Camera Source</th>
              <th className="p-2.5">Detected Label</th>
              <th className="p-2.5">Confidence</th>
              <th className="p-2.5">Provenance Source</th>
              <th className="p-2.5">Validation Status</th>
              <th className="p-2.5 text-right">Human Triage Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-forensic-border/60">
            {filteredSamples.map((sample) => (
              <tr key={sample.sample_id} className="hover:bg-forensic-elevated/40">
                <td className="p-2.5 font-bold text-forensic-text">{sample.sample_id}</td>
                <td className="p-2.5">
                  <div className="flex items-center gap-1.5 text-forensic-text">
                    <Camera className="w-3.5 h-3.5 text-forensic-muted" />
                    <span>{sample.camera_id}</span>
                  </div>
                </td>
                <td className="p-2.5">
                  {editingSampleId === sample.sample_id ? (
                    <div className="flex items-center gap-1">
                      <select
                        value={relabelValue}
                        onChange={(e) => setRelabelValue(e.target.value)}
                        className="bg-forensic-bg border border-forensic-border text-forensic-text px-1 py-0.5 text-xs font-mono"
                      >
                        <option value="person">person</option>
                        <option value="vehicle">vehicle</option>
                        <option value="car">car</option>
                        <option value="truck">truck</option>
                        <option value="motorcycle">motorcycle</option>
                        <option value="bicycle">bicycle</option>
                      </select>
                      <button
                        onClick={() => handleRelabel(sample.sample_id)}
                        className="p-1 bg-signal-safe text-forensic-bg"
                      >
                        <Check className="w-3 h-3" />
                      </button>
                      <button
                        onClick={() => setEditingSampleId(null)}
                        className="p-1 bg-forensic-elevated text-forensic-text border border-forensic-border"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ) : (
                    <span className="px-1.5 py-0.2 bg-forensic-elevated border border-forensic-border text-forensic-text uppercase font-bold text-[9px]">
                      {sample.label}
                    </span>
                  )}
                </td>
                <td className="p-2.5 font-bold text-forensic-text">
                  {(sample.confidence * 100).toFixed(0)}%
                </td>
                <td className="p-2.5 text-[10px] text-forensic-muted">{sample.label_source}</td>
                <td className="p-2.5">
                  <span className={`px-1.5 py-0.2 text-[9px] font-bold border uppercase ${
                    sample.validation_status === 'VALIDATED'
                      ? 'bg-signal-safe/20 text-signal-safe border-signal-safe'
                      : sample.validation_status === 'REJECTED'
                      ? 'bg-signal-threat/20 text-signal-threat border-signal-threat'
                      : 'bg-signal-warning/20 text-signal-warning border-signal-warning'
                  }`}>
                    {sample.validation_status}
                  </span>
                </td>
                <td className="p-2.5 text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    {sample.validation_status !== 'VALIDATED' && (
                      <button
                        onClick={() => handleApprove(sample.sample_id)}
                        disabled={loading}
                        className="px-2 py-0.5 bg-signal-safe/20 hover:bg-signal-safe/30 text-signal-safe border border-signal-safe text-[10px] font-bold transition flex items-center gap-1 cursor-pointer uppercase"
                        title="Accept sample into training pool"
                      >
                        <CheckCircle2 className="w-3 h-3" />
                        <span>ACCEPT</span>
                      </button>
                    )}

                    {sample.validation_status !== 'REJECTED' && (
                      <button
                        onClick={() => handleReject(sample.sample_id)}
                        disabled={loading}
                        className="px-1.5 py-0.5 bg-signal-threat/10 hover:bg-signal-threat/20 text-signal-threat border border-signal-threat text-[10px] transition cursor-pointer"
                        title="Reject sample"
                      >
                        <XCircle className="w-3 h-3" />
                      </button>
                    )}

                    <button
                      onClick={() => {
                        setEditingSampleId(sample.sample_id);
                        setRelabelValue(sample.label);
                      }}
                      className="px-1.5 py-0.5 bg-forensic-elevated hover:bg-forensic-border text-forensic-text border border-forensic-border text-[10px] transition cursor-pointer"
                      title="Correct ground truth label"
                    >
                      <Edit3 className="w-3 h-3" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
