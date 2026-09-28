import React, { useState, useEffect } from 'react';
import {
  X,
  Network,
  Plus,
  Trash2,
  CheckCircle2,
  ArrowRight,
  Clock,
  MapPin,
  RefreshCw
} from 'lucide-react';
import { CameraTopologyRelation, Camera } from '../types';
import { api } from '../services/api';

interface TopologyModalProps {
  isOpen: boolean;
  cameras: Camera[];
  onClose: () => void;
  onUpdated: () => void;
}

export const TopologyModal: React.FC<TopologyModalProps> = ({
  isOpen,
  cameras,
  onClose,
  onUpdated,
}) => {
  const [relations, setRelations] = useState<CameraTopologyRelation[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [sourceCam, setSourceCam] = useState<string>('CAM-01');
  const [destCam, setDestCam] = useState<string>('CAM-02');
  const [minSec, setMinSec] = useState<number>(5.0);
  const [maxSec, setMaxSec] = useState<number>(120.0);
  const [distanceM, setDistanceM] = useState<number>(45.0);
  const [desc, setDesc] = useState<string>('');

  const loadTopology = async () => {
    setLoading(true);
    try {
      const data = await api.getTopology();
      setRelations(data);
    } catch (e) {
      console.error('Failed to load topology:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadTopology();
    }
  }, [isOpen]);

  const handleAddRoute = async (e: React.FormEvent) => {
    e.preventDefault();
    if (sourceCam === destCam) {
      alert('Source and destination camera must be different.');
      return;
    }

    try {
      await api.createTopology({
        source_camera: sourceCam,
        destination_camera: destCam,
        min_transition_seconds: Number(minSec),
        max_transition_seconds: Number(maxSec),
        distance_meters: Number(distanceM),
        direction: 'bidirectional',
        enabled: true,
        description: desc || `Route between ${sourceCam} and ${destCam}`,
      });
      loadTopology();
      onUpdated();
      setDesc('');
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteRoute = async (relationId: string) => {
    try {
      await api.deleteTopology(relationId);
      loadTopology();
      onUpdated();
    } catch (err) {
      console.error(err);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-forensic-surface border border-forensic-border rounded w-full max-w-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Modal Header */}
        <div className="p-4 bg-forensic-elevated border-b border-forensic-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-forensic-bg border border-forensic-border rounded text-forensic-text">
              <Network className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xs font-bold text-forensic-text uppercase tracking-widest font-mono">
                CAMERA SENSOR TOPOLOGY & TRANSIT CONSTRAINTS
              </h2>
              <p className="text-xs text-forensic-muted font-mono">
                Configure physical and logical adjacency routes for candidate cross-camera filtering
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-forensic-muted hover:text-forensic-text hover:bg-forensic-bg rounded transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 overflow-y-auto space-y-5 flex-1 bg-forensic-bg">
          
          {/* Add Topology Route Form */}
          <form onSubmit={handleAddRoute} className="p-4 bg-forensic-surface border border-forensic-border rounded space-y-3">
            <h3 className="text-xs font-bold text-forensic-text uppercase tracking-wider font-mono flex items-center gap-2">
              <Plus className="w-4 h-4 text-forensic-muted" />
              ADD / CONFIGURE INTER-CAMERA ROUTE
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
              <div>
                <label className="text-[10px] text-forensic-muted uppercase block mb-1">Source Camera</label>
                <select
                  value={sourceCam}
                  onChange={(e) => setSourceCam(e.target.value)}
                  className="w-full px-3 py-2 bg-forensic-bg border border-forensic-border rounded text-forensic-text focus:outline-none focus:border-forensic-text"
                >
                  {cameras.map((c) => (
                    <option key={c.camera_id} value={c.camera_id}>
                      {c.camera_id} — {c.camera_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[10px] text-forensic-muted uppercase block mb-1">Destination Camera</label>
                <select
                  value={destCam}
                  onChange={(e) => setDestCam(e.target.value)}
                  className="w-full px-3 py-2 bg-forensic-bg border border-forensic-border rounded text-forensic-text focus:outline-none focus:border-forensic-text"
                >
                  {cameras.map((c) => (
                    <option key={c.camera_id} value={c.camera_id}>
                      {c.camera_id} — {c.camera_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[10px] text-forensic-muted uppercase block mb-1">Min Transit Seconds</label>
                <input
                  type="number"
                  step="1"
                  min="1"
                  value={minSec}
                  onChange={(e) => setMinSec(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-forensic-bg border border-forensic-border rounded text-forensic-text focus:outline-none focus:border-forensic-text"
                />
              </div>

              <div>
                <label className="text-[10px] text-forensic-muted uppercase block mb-1">Max Transit Seconds</label>
                <input
                  type="number"
                  step="1"
                  min="5"
                  value={maxSec}
                  onChange={(e) => setMaxSec(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-forensic-bg border border-forensic-border rounded text-forensic-text focus:outline-none focus:border-forensic-text"
                />
              </div>

              <div>
                <label className="text-[10px] text-forensic-muted uppercase block mb-1">Estimated Distance (Meters)</label>
                <input
                  type="number"
                  step="1"
                  min="1"
                  value={distanceM}
                  onChange={(e) => setDistanceM(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-forensic-bg border border-forensic-border rounded text-forensic-text focus:outline-none focus:border-forensic-text"
                />
              </div>

              <div>
                <label className="text-[10px] text-forensic-muted uppercase block mb-1">Route Description</label>
                <input
                  type="text"
                  placeholder="e.g. Wire fence to river channel path"
                  value={desc}
                  onChange={(e) => setDesc(e.target.value)}
                  className="w-full px-3 py-2 bg-forensic-bg border border-forensic-border rounded text-forensic-text focus:outline-none focus:border-forensic-text"
                />
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                className="px-4 py-2 bg-[#171717] dark:bg-[#F4F1E8] text-[#F4F1E8] dark:text-[#171717] font-mono text-xs font-bold rounded shadow-sm transition flex items-center gap-1.5"
              >
                <Plus className="w-4 h-4" />
                <span>Save Topology Route</span>
              </button>
            </div>
          </form>

          {/* Active Topology Routes List */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-forensic-text uppercase tracking-wider font-mono">
                ACTIVE SENSOR ADJACENCY ROUTES ({relations.length})
              </h3>
              <button
                onClick={loadTopology}
                className="text-xs font-mono text-forensic-text hover:underline flex items-center gap-1"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Refresh</span>
              </button>
            </div>

            <div className="space-y-2">
              {relations.map((rel) => (
                <div
                  key={rel.relation_id}
                  className="p-3 bg-forensic-surface border border-forensic-border rounded flex items-center justify-between gap-3 text-xs font-mono hover:border-forensic-text transition"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 bg-forensic-bg px-3 py-1.5 rounded border border-forensic-border">
                      <span className="font-bold text-forensic-text">{rel.source_camera}</span>
                      <ArrowRight className="w-3.5 h-3.5 text-forensic-muted" />
                      <span className="font-bold text-forensic-text">{rel.destination_camera}</span>
                    </div>

                    <div>
                      <div className="flex items-center gap-2 text-forensic-text">
                        <span>Window: <strong className="text-[#F5A623]">{rel.min_transition_seconds}s - {rel.max_transition_seconds}s</strong></span>
                        <span>•</span>
                        <span>Distance: <strong>{rel.distance_meters}m</strong></span>
                        <span>•</span>
                        <span className="text-emerald-800 dark:text-[#C7FF3D] uppercase text-[10px]">{rel.direction}</span>
                      </div>
                      <p className="text-[10px] text-forensic-muted mt-0.5">{rel.description}</p>
                    </div>
                  </div>

                  <button
                    onClick={() => handleDeleteRoute(rel.relation_id)}
                    className="p-1.5 text-forensic-muted hover:text-[#FF4D4D] hover:bg-rose-500/10 rounded transition"
                    title="Delete Route"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-forensic-elevated border-t border-forensic-border flex items-center justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-forensic-surface hover:bg-forensic-bg text-forensic-text font-mono text-xs rounded border border-forensic-border transition"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
};
