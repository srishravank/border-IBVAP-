import React, { useState, useEffect } from 'react';
import { X, Sliders, Save, RefreshCw, CheckCircle2, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';
import { RiskConfig } from '../types';

interface RiskConfigModalProps {
  onClose: () => void;
  onSaved?: () => void;
}

export const RiskConfigModal: React.FC<RiskConfigModalProps> = ({ onClose, onSaved }) => {
  const [config, setConfig] = useState<RiskConfig | null>(null);
  const [weights, setWeights] = useState<Record<string, number>>({});
  const [thresholds, setThresholds] = useState<Record<string, number>>({});
  const [nightStart, setNightStart] = useState<string>('20:00');
  const [nightEnd, setNightEnd] = useState<string>('05:00');
  const [enabledFactors, setEnabledFactors] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getRiskConfig();
      setConfig(data);
      setWeights(data.weights || {});
      setThresholds(data.thresholds || {});
      setNightStart(data.night_start_time || '20:00');
      setNightEnd(data.night_end_time || '05:00');
      setEnabledFactors(data.enabled_factors || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load risk configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError(null);
      setMessage(null);

      const updated = await api.updateRiskConfig({
        weights,
        thresholds,
        night_start_time: nightStart,
        night_end_time: nightEnd,
        enabled_factors: enabledFactors
      });

      setConfig(updated);
      setMessage(`Configuration saved! New version: ${updated.config_version}`);
      if (onSaved) onSaved();
      setTimeout(() => setMessage(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to update configuration');
    } finally {
      setSaving(false);
    }
  };

  const toggleFactor = (f: string) => {
    setEnabledFactors(prev =>
      prev.includes(f) ? prev.filter(x => x !== f) : [...prev, f]
    );
  };

  const factorLabels: Record<string, string> = {
    ZONE_SENSITIVITY: 'Zone Sensitivity Factor',
    FENCE_CROSSING: 'Virtual Fence Crossing Factor',
    NIGHT_MOVEMENT: 'Night-Time Movement Factor',
    TRAJECTORY: 'Trajectory Dynamics Factor',
    CROSS_CAMERA_JOURNEY: 'Cross-Camera Transit Factor',
    RELATED_VEHICLE_ACTIVITY: 'Related Vehicle Activity Factor',
    BEHAVIOURAL_ANOMALY: 'Behavioural Anomaly (Future Interface)'
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl max-h-[90vh] flex flex-col bg-forensic-surface border border-forensic-border rounded shadow-2xl overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-forensic-border bg-forensic-elevated">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded bg-forensic-bg border border-forensic-border text-forensic-text">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xs font-bold text-forensic-text uppercase tracking-widest font-mono">Risk Engine Configuration</h2>
              <p className="text-xs text-forensic-muted font-mono">
                Active Version: <span className="text-forensic-text font-bold">{config?.config_version || 'v1.0.0'}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded text-forensic-muted hover:text-forensic-text hover:bg-forensic-bg transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSave} className="flex-1 p-6 overflow-y-auto space-y-6 bg-forensic-bg">
          {loading ? (
            <div className="py-12 flex justify-center text-forensic-muted">
              <RefreshCw className="w-6 h-6 animate-spin text-forensic-text" />
            </div>
          ) : (
            <>
              {error && (
                <div className="p-3 rounded bg-rose-500/10 border border-rose-500/30 text-[#FF4D4D] text-xs font-mono flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                  {error}
                </div>
              )}

              {message && (
                <div className="p-3 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-800 dark:text-[#C7FF3D] text-xs font-mono flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                  {message}
                </div>
              )}

              {/* Section 1: Factor Weights */}
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-forensic-text font-mono mb-3">
                  1. Factor Weights (Point Contributions)
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(weights).map(([k, v]) => (
                    <div key={k} className="p-3 rounded bg-forensic-surface border border-forensic-border flex items-center justify-between font-mono">
                      <span className="text-xs text-forensic-text capitalize">{k.replace('_', ' ')}</span>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="1"
                        value={v}
                        onChange={e => setWeights({ ...weights, [k]: parseFloat(e.target.value) || 0 })}
                        className="w-16 px-2 py-1 text-xs font-mono text-center rounded bg-forensic-bg border border-forensic-border text-forensic-text focus:outline-none focus:border-forensic-text"
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* Section 2: Night Surveillance Window */}
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-forensic-text font-mono mb-3">
                  2. Night-Time Surveillance Hours (24h)
                </h3>
                <div className="grid grid-cols-2 gap-4 font-mono">
                  <div>
                    <label className="block text-xs text-forensic-muted mb-1">Night Start Time</label>
                    <input
                      type="text"
                      value={nightStart}
                      onChange={e => setNightStart(e.target.value)}
                      placeholder="20:00"
                      className="w-full px-3 py-2 text-xs font-mono rounded bg-forensic-surface border border-forensic-border text-forensic-text focus:outline-none focus:border-forensic-text"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-forensic-muted mb-1">Night End Time</label>
                    <input
                      type="text"
                      value={nightEnd}
                      onChange={e => setNightEnd(e.target.value)}
                      placeholder="05:00"
                      className="w-full px-3 py-2 text-xs font-mono rounded bg-forensic-surface border border-forensic-border text-forensic-text focus:outline-none focus:border-forensic-text"
                    />
                  </div>
                </div>
              </div>

              {/* Section 3: Enabled Factors */}
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-forensic-text font-mono mb-3">
                  3. Active Modular Intelligence Factors
                </h3>
                <div className="space-y-2 font-mono">
                  {Object.entries(factorLabels).map(([fKey, fName]) => (
                    <label
                      key={fKey}
                      className="flex items-center gap-3 p-3 rounded bg-forensic-surface border border-forensic-border hover:border-forensic-text transition cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={enabledFactors.includes(fKey)}
                        onChange={() => toggleFactor(fKey)}
                        className="rounded border-forensic-border text-forensic-text focus:ring-0"
                      />
                      <span className="text-xs text-forensic-text">{fName}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-forensic-border">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-xs font-mono rounded bg-forensic-surface hover:bg-forensic-bg text-forensic-muted hover:text-forensic-text border border-forensic-border transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-5 py-2 text-xs font-mono font-bold rounded bg-[#171717] dark:bg-[#F4F1E8] text-[#F4F1E8] dark:text-[#171717] flex items-center gap-1.5 transition shadow-sm"
                >
                  <Save className="w-3.5 h-3.5" />
                  {saving ? 'Saving Version...' : 'Apply & Version'}
                </button>
              </div>
            </>
          )}
        </form>
      </div>
    </div>
  );
};
