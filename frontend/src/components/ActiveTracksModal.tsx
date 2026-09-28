import React, { useState, useEffect } from 'react';
import { X, Crosshair, User, Car, Activity, MapPin, RefreshCw, Eye } from 'lucide-react';
import { TrackedObject, AIPerformanceStats } from '../types';
import { api } from '../services/api';

interface ActiveTracksModalProps {
  cameraId: string | null;
  onClose: () => void;
}

export const ActiveTracksModal: React.FC<ActiveTracksModalProps> = ({ cameraId, onClose }) => {
  const [tracks, setTracks] = useState<TrackedObject[]>([]);
  const [perf, setPerf] = useState<AIPerformanceStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedTrack, setSelectedTrack] = useState<TrackedObject | null>(null);

  useEffect(() => {
    if (!cameraId) return;

    const fetchTracks = async () => {
      try {
        setLoading(true);
        const [tracksData, perfData] = await Promise.all([
          api.getCameraTracks(cameraId),
          api.getCameraPerformance(cameraId),
        ]);
        setTracks(tracksData);
        setPerf(perfData);
        if (tracksData.length > 0 && !selectedTrack) {
          setSelectedTrack(tracksData[0]);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchTracks();
    const interval = setInterval(fetchTracks, 1500);
    return () => clearInterval(interval);
  }, [cameraId]);

  if (!cameraId) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-forensic-surface border border-forensic-border rounded w-full max-w-4xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        
        {/* Header */}
        <div className="p-4 bg-forensic-elevated border-b border-forensic-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-forensic-bg text-forensic-text border border-forensic-border rounded">
              <Crosshair className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xs font-bold text-forensic-text uppercase tracking-widest font-mono">
                  ACTIVE BYTETRACKS & TRAJECTORY INSPECTOR
                </h2>
                <span className="px-2 py-0.5 bg-forensic-bg text-forensic-text font-mono text-xs font-bold rounded border border-forensic-border">
                  {cameraId}
                </span>
              </div>
              <p className="text-[11px] text-forensic-muted mt-0.5 font-mono">
                Model: {perf?.model_name || 'YOLO'} | Latency: {perf?.total_pipeline_ms?.toFixed(1) || '0.0'} ms | Active Targets: {tracks.length}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-forensic-muted hover:text-forensic-text rounded transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-hidden grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-forensic-border bg-forensic-bg">
          
          {/* Tracks List */}
          <div className="p-4 overflow-y-auto space-y-2.5 max-h-[500px]">
            <div className="flex items-center justify-between text-xs font-mono text-forensic-muted mb-1 px-1">
              <span>TARGETS ({tracks.length})</span>
              <span>CONFIDENCE</span>
            </div>

            {tracks.length === 0 ? (
              <div className="p-8 text-center text-xs font-mono text-forensic-muted">
                No active targets currently tracked by ByteTrack for this camera.
              </div>
            ) : (
              tracks.map((track) => {
                const isPerson = track.object_type === 'person';
                const isSelected = selectedTrack?.track_id === track.track_id;

                return (
                  <div
                    key={track.track_id}
                    onClick={() => setSelectedTrack(track)}
                    className={`p-3 rounded border transition cursor-pointer flex items-center justify-between ${
                      isSelected
                        ? 'bg-forensic-surface border-forensic-text shadow-sm'
                        : 'bg-forensic-surface/60 hover:bg-forensic-surface border-forensic-border'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`p-2 rounded border border-forensic-border ${
                          isPerson ? 'bg-[#C7FF3D]/10 text-emerald-800 dark:text-[#C7FF3D]' : 'bg-forensic-bg text-forensic-text'
                        }`}
                      >
                        {isPerson ? <User className="w-4 h-4" /> : <Car className="w-4 h-4" />}
                      </div>
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono font-bold text-xs text-forensic-text">
                            {track.formatted_id}
                          </span>
                          <span className="text-[10px] uppercase px-1.5 py-0.2 rounded bg-forensic-bg text-forensic-muted border border-forensic-border font-mono">
                            {track.class_name}
                          </span>
                        </div>
                        <span className="text-[10px] text-forensic-muted font-mono block mt-0.5">
                          Centroid: [{track.center[0]}, {track.center[1]}] • Age: {track.age}f
                        </span>
                      </div>
                    </div>

                    <div className="text-right font-mono">
                      <span className="text-xs font-bold text-forensic-text">
                        {(track.confidence * 100).toFixed(1)}%
                      </span>
                      <span className="text-[9px] text-forensic-muted block">
                        {track.trajectory.length} pts trail
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Selected Track Detailed Trajectory Inspector */}
          <div className="p-4 overflow-y-auto max-h-[500px] flex flex-col justify-between bg-forensic-surface">
            {selectedTrack ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-forensic-border">
                  <div>
                    <span className="text-[10px] font-mono uppercase text-forensic-muted">Selected Track Profile</span>
                    <h3 className="text-sm font-bold text-forensic-text font-mono flex items-center gap-2 mt-0.5">
                      <span>{selectedTrack.formatted_id}</span>
                      <span className="text-xs font-normal text-forensic-muted uppercase">
                        ({selectedTrack.class_name})
                      </span>
                    </h3>
                  </div>

                  <span className="px-2.5 py-1 rounded bg-[#C7FF3D]/10 text-emerald-800 dark:text-[#C7FF3D] border border-emerald-500/30 text-xs font-mono font-bold">
                    STATE: {selectedTrack.state}
                  </span>
                </div>

                {/* Bounding Box & Coordinates */}
                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="bg-forensic-bg p-2.5 rounded border border-forensic-border">
                    <span className="text-forensic-muted block text-[10px] uppercase">Bounding Box [x1, y1, x2, y2]</span>
                    <span className="text-forensic-text mt-1 block">
                      [{selectedTrack.bbox.join(', ')}]
                    </span>
                  </div>

                  <div className="bg-forensic-bg p-2.5 rounded border border-forensic-border">
                    <span className="text-forensic-muted block text-[10px] uppercase">Current Centroid [cx, cy]</span>
                    <span className="text-forensic-text font-bold mt-1 block">
                      [{selectedTrack.center[0]}, {selectedTrack.center[1]}]
                    </span>
                  </div>
                </div>

                {/* Trajectory History */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-mono text-forensic-text font-bold">
                      OBSERVED TRAJECTORY TRAIL ({selectedTrack.trajectory.length} COORDINATES)
                    </span>
                    <span className="text-[10px] font-mono text-forensic-muted">Chronological [cx, cy]</span>
                  </div>

                  <div className="bg-forensic-bg border border-forensic-border rounded p-3 max-h-48 overflow-y-auto font-mono text-[11px] text-forensic-muted space-y-1">
                    {selectedTrack.trajectory.map((pt, idx) => (
                      <div key={idx} className="flex items-center justify-between hover:text-forensic-text transition">
                        <span>Point #{idx + 1}</span>
                        <span className="text-forensic-text">[{pt[0]}, {pt[1]}]</span>
                      </div>
                    ))}
                  </div>
                </div>

              </div>
            ) : (
              <div className="p-12 text-center text-xs text-forensic-muted font-mono">
                Select a tracked target to view trajectory history.
              </div>
            )}

            <div className="pt-4 border-t border-forensic-border flex items-center justify-between text-[11px] font-mono text-forensic-muted">
              <span>Phase 3 Ready Schema</span>
              <span>ByteTrack Kalman Association</span>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};
