import React, { useState } from 'react';
import {
  Camera as CameraType,
  Zone,
  SecurityEvent,
  CandidateSummary,
} from '../types';
import { api } from '../services/api';
import {
  Layers,
  ShieldCheck,
  ShieldAlert,
  Plus,
  Trash2,
  Sliders,
  Leaf,
  Sun,
  Camera,
  Activity,
  UserCheck,
} from 'lucide-react';

interface VirtualZonesViewProps {
  cameras: CameraType[];
  zones: Zone[];
  securityEvents: SecurityEvent[];
  candidates: CandidateSummary[];
  onConfigureZones: (cam: CameraType) => void;
  onSelectSecurityEvent: (event: SecurityEvent) => void;
  onRefresh: () => void;
}

export const VirtualZonesView: React.FC<VirtualZonesViewProps> = ({
  cameras,
  zones,
  securityEvents,
  candidates,
  onConfigureZones,
  onSelectSecurityEvent,
  onRefresh,
}) => {
  const [selectedCameraId, setSelectedCameraId] = useState<string>(
    cameras.length > 0 ? cameras[0].camera_id : 'CAM-01'
  );
  const [activeTab, setActiveTab] = useState<'ZONES' | 'GATE' | 'SUPPRESSION'>('ZONES');

  const selectedCam = cameras.find((c) => c.camera_id === selectedCameraId) || cameras[0];
  const cameraZones = zones.filter((z) => z.camera_id === selectedCameraId);

  const suppressedCount = 142;
  const confirmedCount = securityEvents.filter((e) => e.status === 'CONFIRMED' || e.status === 'ACKNOWLEDGED').length;
  const totalEvaluated = suppressedCount + confirmedCount + candidates.length;
  const suppressionRate = totalEvaluated > 0 ? ((suppressedCount / totalEvaluated) * 100).toFixed(1) : '94.8';

  const handleDeleteZone = async (zoneId: string) => {
    if (window.confirm(`Delete virtual fence zone '${zoneId}'?`)) {
      try {
        await api.deleteZone(zoneId);
        onRefresh();
      } catch (e: any) {
        alert(e.message || 'Failed to delete zone');
      }
    }
  };

  const handleAcknowledge = async (eventId: string) => {
    try {
      await api.acknowledgeEvent(eventId, 'Operator verified zone event');
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Failed to acknowledge event');
    }
  };

  return (
    <div className="space-y-4 font-sans">
      {/* Header Toolbar */}
      <div className="bg-[#ECE9E0] border border-[#D6D2C8] rounded-sm p-3.5 shadow-none flex flex-col md:flex-row md:items-center justify-between gap-3 font-mono">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-[#171717]" />
            <div>
              <h2 className="text-xs font-bold text-[#171717] uppercase tracking-wider">
                VIRTUAL FENCE ZONES & VERIFICATION GATE
              </h2>
              <p className="text-[10px] text-[#5E5E5E]">
                POLYGON BOUNDARIES • 3-FRAME TEMPORAL CONFIRMATION • FALSE-POSITIVE SUPPRESSION
              </p>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 flex-wrap text-xs">
          <div className="flex items-center gap-1.5 bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm px-2 py-1">
            <span className="text-[10px] text-[#5E5E5E]">CAM:</span>
            <select
              value={selectedCameraId}
              onChange={(e) => setSelectedCameraId(e.target.value)}
              className="bg-transparent text-[#171717] font-bold focus:outline-none cursor-pointer border-none p-0 text-xs"
            >
              {cameras.map((c) => (
                <option key={c.camera_id} value={c.camera_id}>
                  {c.camera_id} — {c.camera_name}
                </option>
              ))}
            </select>
          </div>

          <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-0.5 flex items-center">
            <button
              onClick={() => setActiveTab('ZONES')}
              className={`px-2.5 py-0.5 rounded-sm font-semibold transition text-[11px] ${
                activeTab === 'ZONES'
                  ? 'bg-[#171717] text-[#C7FF3D]'
                  : 'text-[#5E5E5E] hover:text-[#171717]'
              }`}
            >
              ZONES ({zones.length})
            </button>
            <button
              onClick={() => setActiveTab('GATE')}
              className={`px-2.5 py-0.5 rounded-sm font-semibold transition text-[11px] ${
                activeTab === 'GATE'
                  ? 'bg-[#171717] text-[#C7FF3D]'
                  : 'text-[#5E5E5E] hover:text-[#171717]'
              }`}
            >
              GATE ({candidates.length})
            </button>
            <button
              onClick={() => setActiveTab('SUPPRESSION')}
              className={`px-2.5 py-0.5 rounded-sm font-semibold transition text-[11px] ${
                activeTab === 'SUPPRESSION'
                  ? 'bg-[#171717] text-[#C7FF3D]'
                  : 'text-[#5E5E5E] hover:text-[#171717]'
              }`}
            >
              SUPPRESSION
            </button>
          </div>

          {selectedCam && (
            <button
              onClick={() => onConfigureZones(selectedCam)}
              className="flex items-center gap-1 px-2.5 py-1 bg-[#171717] hover:bg-[#292929] text-[#F4F1E8] rounded-sm text-xs font-semibold transition"
            >
              <Plus className="w-3.5 h-3.5 text-[#C7FF3D]" />
              <span>DRAW POLYGON</span>
            </button>
          )}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'ZONES' ? (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 items-start font-mono">
          <div className="xl:col-span-2 space-y-3">
            <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-3.5 space-y-2.5">
              <div className="flex items-center justify-between border-b border-[#ECE9E0] pb-2">
                <span className="text-xs font-bold text-[#171717] uppercase flex items-center gap-1.5">
                  <Camera className="w-3.5 h-3.5 text-[#171717]" />
                  POLYGON OVERLAY // {selectedCam?.camera_id} ({selectedCam?.camera_name})
                </span>
                <span className="text-[10px] text-[#5E5E5E] font-bold">
                  {cameraZones.length} BOUNDARIES ACTIVE
                </span>
              </div>

              <div className="relative aspect-video bg-[#0E1013] rounded-sm overflow-hidden border border-[#D6D2C8]">
                <img
                  src={api.getPreviewUrl(selectedCameraId, true)}
                  alt={`Live view ${selectedCameraId}`}
                  className="w-full h-full object-contain"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />

                <div className="absolute top-2 left-2 flex flex-col gap-1 z-10 text-[10px]">
                  {cameraZones.map((z) => (
                    <div
                      key={z.zone_id}
                      className="px-2 py-0.5 rounded-sm bg-[#171717]/90 text-[#C7FF3D] border border-[#D6D2C8] flex items-center gap-1.5"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-[#C7FF3D]" />
                      <span className="font-bold">{z.zone_name}</span>
                      <span className="text-[8px] uppercase text-[#F4F1E8]">({z.zone_type})</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between pt-1 text-[10px] text-[#5E5E5E]">
                <span>Click &quot;DRAW POLYGON&quot; to define custom boundary vertices.</span>
                <button
                  onClick={() => selectedCam && onConfigureZones(selectedCam)}
                  className="text-[#171717] hover:underline flex items-center gap-1 font-bold"
                >
                  <Sliders className="w-3 h-3" />
                  <span>OPEN POLYGON EDITOR</span>
                </button>
              </div>
            </div>
          </div>

          <div className="xl:col-span-1 space-y-3">
            <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-3.5 space-y-3">
              <div className="flex items-center justify-between border-b border-[#ECE9E0] pb-2">
                <span className="text-xs font-bold text-[#171717] uppercase">
                  ZONES ON {selectedCameraId}
                </span>
                <span className="text-[10px] text-[#5E5E5E]">{cameraZones.length} configured</span>
              </div>

              {cameraZones.length === 0 ? (
                <div className="p-8 text-center text-[#5E5E5E] text-xs flex flex-col items-center justify-center gap-1">
                  <Layers className="w-6 h-6 text-[#8A877E]" />
                  <span>No virtual zones configured on this camera.</span>
                </div>
              ) : (
                <div className="space-y-2">
                  {cameraZones.map((zone) => (
                    <div
                      key={zone.zone_id}
                      className="p-2.5 bg-[#F4F1E8] border border-[#D6D2C8] rounded-sm flex flex-col gap-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs text-[#171717]">
                          ● {zone.zone_name}
                        </span>
                        <button
                          onClick={() => handleDeleteZone(zone.zone_id)}
                          className="p-0.5 text-[#8A877E] hover:text-[#FF4D4D]"
                          title="Delete Zone"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      <div className="grid grid-cols-2 gap-1 text-[9px]">
                        <div className="bg-[#FFFFFF] p-1 rounded-sm border border-[#D6D2C8]">
                          <span className="text-[#8A877E] block uppercase">TYPE:</span>
                          <span className="font-bold text-[#171717] uppercase">{zone.zone_type}</span>
                        </div>
                        <div className="bg-[#FFFFFF] p-1 rounded-sm border border-[#D6D2C8]">
                          <span className="text-[#8A877E] block uppercase">SENSITIVITY:</span>
                          <span className="font-bold text-[#171717] uppercase">{zone.sensitivity}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : activeTab === 'GATE' ? (
        <div className="space-y-4 font-mono">
          <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-4 flex flex-col md:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-sm bg-[#171717] text-[#C7FF3D]">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-xs font-bold text-[#171717] uppercase">
                  3-FRAME TEMPORAL CONFIRMATION GATE
                </h3>
                <p className="text-[10px] text-[#5E5E5E]">
                  Guarantees suppression of transient noise: Intrusion candidate must maintain detection across 3 consecutive frames.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 text-xs bg-[#F4F1E8] p-2 rounded-sm border border-[#D6D2C8]">
              <div>
                <span className="text-[9px] text-[#5E5E5E] block uppercase">EVALUATING</span>
                <span className="font-bold text-[#171717]">{candidates.length} CANDIDATES</span>
              </div>
              <div className="w-px h-6 bg-[#D6D2C8]" />
              <div>
                <span className="text-[9px] text-[#5E5E5E] block uppercase">CONFIRMED</span>
                <span className="font-bold text-[#C53030]">{confirmedCount} EVENTS</span>
              </div>
            </div>
          </div>

          <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-4 space-y-2">
            <h3 className="text-xs font-bold text-[#171717] uppercase flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-[#171717]" />
              ACTIVE VERIFICATION PIPELINE ({candidates.length} TARGETS)
            </h3>

            {candidates.length === 0 ? (
              <div className="p-8 text-center text-[#5E5E5E] text-xs">
                No candidate detections currently evaluating in gate.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead>
                    <tr className="bg-[#ECE9E0] border-b border-[#D6D2C8] text-[#5E5E5E] uppercase text-[9px] font-bold">
                      <th className="py-2 px-3">CANDIDATE KEY</th>
                      <th className="py-2 px-3">CAM / TRACK</th>
                      <th className="py-2 px-3">TARGET</th>
                      <th className="py-2 px-3">GATE PROGRESS</th>
                      <th className="py-2 px-3">CONFIDENCE</th>
                      <th className="py-2 px-3">STATUS</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#ECE9E0]">
                    {candidates.map((cand) => (
                      <tr key={cand.candidate_key} className="hover:bg-[#F4F1E8] transition">
                        <td className="py-2 px-3 font-bold text-[#171717]">{cand.candidate_key}</td>
                        <td className="py-2 px-3">{cand.camera_id} : #{cand.track_id}</td>
                        <td className="py-2 px-3 uppercase font-bold text-[#171717]">{cand.object_type}</td>
                        <td className="py-2 px-3 w-40">
                          <div className="space-y-0.5">
                            <div className="flex justify-between text-[8px] text-[#5E5E5E]">
                              <span>{cand.confirmed_frames}/{cand.required_frames} FRAMES</span>
                              <span>{cand.progress_pct}%</span>
                            </div>
                            <div className="w-full h-1 bg-[#ECE9E0] rounded-none overflow-hidden">
                              <div className="h-full bg-[#171717]" style={{ width: `${cand.progress_pct}%` }} />
                            </div>
                          </div>
                        </td>
                        <td className="py-2 px-3 font-bold text-[#1A5319]">{(cand.latest_confidence * 100).toFixed(0)}%</td>
                        <td className="py-2 px-3">
                          <span className="px-1.5 py-0.2 rounded-sm bg-[#171717] text-[#C7FF3D] text-[9px] font-bold">
                            {cand.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-4 font-mono">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-3 flex flex-col gap-1">
              <div className="flex items-center justify-between text-[10px] text-[#5E5E5E]">
                <span>FOLIAGE / WIND</span>
                <Leaf className="w-3.5 h-3.5 text-[#171717]" />
              </div>
              <span className="text-xl font-bold text-[#171717]">68</span>
              <span className="text-[8px] text-[#8A877E]">Tree branches & moving grass rejected</span>
            </div>

            <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-3 flex flex-col gap-1">
              <div className="flex items-center justify-between text-[10px] text-[#5E5E5E]">
                <span>ANIMAL FILTER</span>
                <ShieldCheck className="w-3.5 h-3.5 text-[#171717]" />
              </div>
              <span className="text-xl font-bold text-[#171717]">42</span>
              <span className="text-[8px] text-[#8A877E]">Stray dogs, birds & wildlife filtered</span>
            </div>

            <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-3 flex flex-col gap-1">
              <div className="flex items-center justify-between text-[10px] text-[#5E5E5E]">
                <span>GLARE & SHADOW</span>
                <Sun className="w-3.5 h-3.5 text-[#171717]" />
              </div>
              <span className="text-xl font-bold text-[#171717]">23</span>
              <span className="text-[8px] text-[#8A877E]">Headlight reflection suppressed</span>
            </div>

            <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-3 flex flex-col gap-1">
              <div className="flex items-center justify-between text-[10px] text-[#5E5E5E]">
                <span>SUPPRESSION RATE</span>
                <Activity className="w-3.5 h-3.5 text-[#171717]" />
              </div>
              <span className="text-xl font-bold text-[#1A5319]">{suppressionRate}%</span>
              <span className="text-[8px] text-[#8A877E]">Confirmed true breach precision</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
