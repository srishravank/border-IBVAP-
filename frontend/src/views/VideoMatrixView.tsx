import React, { useState, useEffect } from 'react';
import {
  Camera as CameraType,
  Incident,
  TrackedObject,
  AIPerformanceStats,
  Zone,
} from '../types';
import { api } from '../services/api';
import {
  Camera,
  Grid,
  Maximize2,
  Play,
  Square,
  Eye,
  Sliders,
  Activity,
  Cpu,
  Plus,
  ShieldAlert,
  Search,
  Move,
  ZoomIn,
  ZoomOut,
  Zap,
} from 'lucide-react';

interface VideoMatrixViewProps {
  cameras: CameraType[];
  incidents: Incident[];
  zones: Zone[];
  onToggleIngestion: (id: string, isLive: boolean) => void;
  onInspectTracks: (id: string) => void;
  onConfigureZones: (cam: CameraType) => void;
  onSelectIncident: (incidentId: string) => void;
  onAddCamera: () => void;
  onRefresh: () => void;
}

export const VideoMatrixView: React.FC<VideoMatrixViewProps> = ({
  cameras,
  incidents,
  zones,
  onToggleIngestion,
  onInspectTracks,
  onConfigureZones,
  onSelectIncident,
  onAddCamera,
}) => {
  const [layout, setLayout] = useState<'1x1' | '2x2' | '3x3' | 'auto'>('auto');
  const [showAnnotations, setShowAnnotations] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedCameraId, setSelectedCameraId] = useState<string | null>(
    cameras.length > 0 ? cameras[0].camera_id : null
  );

  const [cameraTracks, setCameraTracks] = useState<TrackedObject[]>([]);
  const [cameraPerf, setCameraPerf] = useState<AIPerformanceStats | null>(null);
  const [ptzZoom, setPtzZoom] = useState<number>(100);
  const [ptzPan, setPtzPan] = useState<number>(0);
  const [ptzTilt, setPtzTilt] = useState<number>(0);

  const filteredCameras = cameras.filter((cam) => {
    if (statusFilter !== 'ALL') {
      if (statusFilter === 'ONLINE' && cam.status !== 'ONLINE') return false;
      if (statusFilter === 'ALERT') {
        const hasAlert = incidents.some(
          (i) => i.cameras_involved?.includes(cam.camera_id) && i.status !== 'CLOSED'
        );
        if (!hasAlert) return false;
      }
      if (statusFilter === 'OFFLINE' && cam.status !== 'OFFLINE') return false;
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchId = cam.camera_id.toLowerCase().includes(q);
      const matchName = cam.camera_name.toLowerCase().includes(q);
      const matchLoc = cam.location.toLowerCase().includes(q);
      if (!matchId && !matchName && !matchLoc) return false;
    }
    return true;
  });

  const selectedCam = cameras.find((c) => c.camera_id === selectedCameraId) || cameras[0];

  useEffect(() => {
    if (!selectedCameraId) return;

    let isMounted = true;
    const loadDetails = async () => {
      try {
        const [tracksData, perfData] = await Promise.all([
          api.getCameraTracks(selectedCameraId).catch(() => []),
          api.getCameraPerformance(selectedCameraId).catch(() => null),
        ]);
        if (isMounted) {
          setCameraTracks(tracksData);
          setCameraPerf(perfData);
        }
      } catch (e) {
        console.error('Error fetching camera details:', e);
      }
    };

    loadDetails();
    const interval = setInterval(loadDetails, 2000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [selectedCameraId]);

  const getGridCols = () => {
    if (layout === '1x1') return 'grid-cols-1';
    if (layout === '2x2') return 'grid-cols-1 md:grid-cols-2';
    if (layout === '3x3') return 'grid-cols-1 md:grid-cols-2 xl:grid-cols-3';
    return filteredCameras.length <= 1
      ? 'grid-cols-1'
      : filteredCameras.length <= 2
      ? 'grid-cols-1 md:grid-cols-2'
      : 'grid-cols-1 md:grid-cols-2 xl:grid-cols-3';
  };

  return (
    <div className="space-y-4 font-sans">
      {/* Top Controls Toolbar */}
      <div className="bg-[#ECE9E0] border border-[#D6D2C8] rounded-sm p-3.5 shadow-none flex flex-col md:flex-row md:items-center justify-between gap-3 font-mono">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Camera className="w-4 h-4 text-[#171717]" />
            <div>
              <h2 className="text-xs font-bold text-[#171717] uppercase tracking-wider">
                MULTI-CAMERA CCTV MATRIX & AI PERCEPTION
              </h2>
              <p className="text-[10px] text-[#5E5E5E]">
                LIVE RTSP/MJPEG STREAMS • BYTETRACK OBJECT TRAJECTORIES • PTZ COCKPIT
              </p>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 flex-wrap text-xs">
          <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-0.5 flex items-center">
            {['ALL', 'ONLINE', 'ALERT', 'OFFLINE'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-2 py-0.5 rounded-sm transition text-[10px] font-semibold ${
                  statusFilter === st
                    ? 'bg-[#171717] text-[#C7FF3D]'
                    : 'text-[#5E5E5E] hover:text-[#171717]'
                }`}
              >
                {st}
              </button>
            ))}
          </div>

          <div className="relative">
            <input
              type="text"
              placeholder="SEARCH CAMERA..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm pl-6 pr-2 py-0.5 text-[11px] text-[#171717] placeholder-[#8A877E] focus:outline-none focus:border-[#171717] w-32 sm:w-40"
            />
            <Search className="w-3 h-3 text-[#8A877E] absolute left-1.5 top-1.5" />
          </div>

          <button
            onClick={() => setShowAnnotations(!showAnnotations)}
            className={`px-2 py-0.5 rounded-sm text-[10px] font-bold border transition ${
              showAnnotations
                ? 'bg-[#171717] text-[#C7FF3D] border-[#171717]'
                : 'bg-[#FFFFFF] text-[#5E5E5E] border-[#D6D2C8]'
            }`}
          >
            {showAnnotations ? '● ANNOTATIONS ON' : '○ RAW'}
          </button>

          <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-0.5 flex items-center">
            <button
              onClick={() => setLayout('auto')}
              className={`p-1 rounded-sm ${layout === 'auto' ? 'bg-[#171717] text-[#C7FF3D]' : 'text-[#5E5E5E]'}`}
              title="Auto Grid"
            >
              <Grid className="w-3 h-3" />
            </button>
            <button
              onClick={() => setLayout('1x1')}
              className={`p-1 rounded-sm ${layout === '1x1' ? 'bg-[#171717] text-[#C7FF3D]' : 'text-[#5E5E5E]'}`}
              title="Focus 1x1"
            >
              <Maximize2 className="w-3 h-3" />
            </button>
            <button
              onClick={() => setLayout('2x2')}
              className={`px-1.5 py-0.5 text-[9px] font-bold rounded-sm ${layout === '2x2' ? 'bg-[#171717] text-[#C7FF3D]' : 'text-[#5E5E5E]'}`}
            >
              2x2
            </button>
            <button
              onClick={() => setLayout('3x3')}
              className={`px-1.5 py-0.5 text-[9px] font-bold rounded-sm ${layout === '3x3' ? 'bg-[#171717] text-[#C7FF3D]' : 'text-[#5E5E5E]'}`}
            >
              3x3
            </button>
          </div>

          <button
            onClick={onAddCamera}
            className="flex items-center gap-1 px-2.5 py-1 bg-[#171717] hover:bg-[#292929] text-[#F4F1E8] rounded-sm text-xs font-semibold transition"
          >
            <Plus className="w-3.5 h-3.5 text-[#C7FF3D]" />
            <span>ADD CAM</span>
          </button>
        </div>
      </div>

      {/* Main Split Layout */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-4 items-start font-mono">
        <div className="xl:col-span-3 space-y-4">
          <div className={`grid gap-3 ${getGridCols()}`}>
            {filteredCameras.map((camera) => {
              const isLive = camera.status !== 'OFFLINE';
              const isSelected = selectedCameraId === camera.camera_id;
              const camIncidents = incidents.filter(
                (i) =>
                  i.cameras_involved?.includes(camera.camera_id) &&
                  i.status !== 'CLOSED'
              );

              return (
                <div
                  key={camera.camera_id}
                  onClick={() => setSelectedCameraId(camera.camera_id)}
                  className={`bg-[#FFFFFF] rounded-sm border overflow-hidden transition-all shadow-none flex flex-col cursor-pointer ${
                    isSelected
                      ? 'border-[#171717] ring-1 ring-[#171717]'
                      : camIncidents.length > 0
                      ? 'border-[#FF4D4D]'
                      : 'border-[#D6D2C8] hover:border-[#171717]/60'
                  }`}
                >
                  <div className="bg-[#ECE9E0] px-3 py-1.5 border-b border-[#D6D2C8] flex items-center justify-between">
                    <div className="flex items-center gap-2 min-w-0">
                      <span
                        className={`w-2 h-2 rounded-full flex-shrink-0 ${
                          isLive ? 'bg-[#C7FF3D]' : 'bg-[#FF4D4D]'
                        }`}
                      />
                      <span className="font-bold text-xs text-[#171717] truncate">
                        {camera.camera_id} / {camera.camera_name.toUpperCase()}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 text-[10px]">
                      <span className="font-bold text-[#171717]">● {camera.status}</span>
                      <span className="text-[#5E5E5E]">|</span>
                      <span className="font-semibold text-[#171717]">
                        {camera.fps?.toFixed(1) || '07.4'} FPS
                      </span>
                    </div>
                  </div>

                  <div className="relative aspect-video bg-[#0E1013] flex items-center justify-center group overflow-hidden border-b border-[#D6D2C8]">
                    {isLive ? (
                      <img
                        src={api.getPreviewUrl(camera.camera_id, showAnnotations)}
                        alt={`Live feed from ${camera.camera_id}`}
                        className="w-full h-full object-contain"
                        style={{
                          transform: isSelected
                            ? `scale(${ptzZoom / 100}) translate(${ptzPan}px, ${ptzTilt}px)`
                            : 'none',
                          transition: 'transform 0.1s ease-out',
                        }}
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
                      />
                    ) : (
                      <div className="flex flex-col items-center justify-center text-[#8A877E] gap-1">
                        <Camera className="w-8 h-8 text-[#5E5E5E]" />
                        <span className="text-xs font-semibold text-[#F4F1E8]">STANDBY // OFFLINE</span>
                      </div>
                    )}

                    {camIncidents.length > 0 && (
                      <div className="absolute top-2 left-2 flex flex-col gap-1 z-10">
                        {camIncidents.map((inc) => (
                          <button
                            key={inc.incident_id}
                            onClick={(e) => {
                              e.stopPropagation();
                              onSelectIncident(inc.incident_id);
                            }}
                            className="px-2 py-0.5 rounded-sm bg-[#FF4D4D] text-[#FFFFFF] text-[9px] font-bold flex items-center gap-1"
                          >
                            <ShieldAlert className="w-2.5 h-2.5" />
                            <span>{inc.incident_id}</span>
                          </button>
                        ))}
                      </div>
                    )}

                    <div className="absolute bottom-2 right-2 flex items-center gap-1 bg-[#171717]/90 p-1 rounded-sm opacity-0 group-hover:opacity-100 transition-opacity z-10 text-[#F4F1E8]">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onInspectTracks(camera.camera_id);
                        }}
                        className="p-1 hover:text-[#C7FF3D] transition"
                        title="Inspect Tracks"
                      >
                        <Eye className="w-3 h-3" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onConfigureZones(camera);
                        }}
                        className="p-1 hover:text-[#C7FF3D] transition"
                        title="Configure Zones"
                      >
                        <Sliders className="w-3 h-3" />
                      </button>
                    </div>
                  </div>

                  <div className="bg-[#ECE9E0] px-3 py-1.5 flex items-center justify-between text-[10px] text-[#5E5E5E]">
                    <span className="truncate">{camera.location}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggleIngestion(camera.camera_id, isLive);
                      }}
                      className={`px-2 py-0.5 rounded-sm font-bold transition ${
                        isLive
                          ? 'bg-[#171717] text-[#FF4D4D] hover:bg-[#292929]'
                          : 'bg-[#171717] text-[#C7FF3D] hover:bg-[#292929]'
                      }`}
                    >
                      {isLive ? 'STOP' : 'START'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Side: Inspector */}
        <div className="xl:col-span-1 space-y-3 sticky top-24">
          {selectedCam ? (
            <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-3.5 space-y-3">
              <div className="border-b border-[#ECE9E0] pb-2 flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-bold text-[#5E5E5E] block">
                    CHANNEL INSPECTOR
                  </span>
                  <h3 className="text-xs font-bold text-[#171717]">
                    {selectedCam.camera_id} ({selectedCam.camera_name})
                  </h3>
                </div>
                <button
                  onClick={() => onConfigureZones(selectedCam)}
                  className="px-2 py-0.5 bg-[#FFFFFF] hover:bg-[#171717] hover:text-[#C7FF3D] text-[#171717] border border-[#D6D2C8] rounded-sm text-[10px] font-semibold"
                >
                  ZONES
                </button>
              </div>

              {/* PTZ Controls */}
              <div className="bg-[#F4F1E8] border border-[#D6D2C8] rounded-sm p-2.5 space-y-1.5 text-xs">
                <div className="flex items-center justify-between font-bold text-[#171717]">
                  <span className="flex items-center gap-1">
                    <Move className="w-3 h-3 text-[#171717]" />
                    PTZ COCKPIT
                  </span>
                  <span className="text-[#171717]">{ptzZoom}%</span>
                </div>

                <div className="grid grid-cols-3 gap-1 pt-1">
                  <div />
                  <button
                    onClick={() => setPtzTilt((t) => t - 10)}
                    className="p-1 bg-[#FFFFFF] hover:bg-[#171717] hover:text-[#F4F1E8] text-[#171717] border border-[#D6D2C8] rounded-sm text-[10px] text-center"
                  >
                    ▲ UP
                  </button>
                  <div />

                  <button
                    onClick={() => setPtzPan((p) => p - 10)}
                    className="p-1 bg-[#FFFFFF] hover:bg-[#171717] hover:text-[#F4F1E8] text-[#171717] border border-[#D6D2C8] rounded-sm text-[10px] text-center"
                  >
                    ◀ L
                  </button>
                  <button
                    onClick={() => {
                      setPtzPan(0);
                      setPtzTilt(0);
                      setPtzZoom(100);
                    }}
                    className="p-1 bg-[#171717] text-[#C7FF3D] rounded-sm text-[9px] text-center font-bold"
                  >
                    RESET
                  </button>
                  <button
                    onClick={() => setPtzPan((p) => p + 10)}
                    className="p-1 bg-[#FFFFFF] hover:bg-[#171717] hover:text-[#F4F1E8] text-[#171717] border border-[#D6D2C8] rounded-sm text-[10px] text-center"
                  >
                    R ▶
                  </button>

                  <div />
                  <button
                    onClick={() => setPtzTilt((t) => t + 10)}
                    className="p-1 bg-[#FFFFFF] hover:bg-[#171717] hover:text-[#F4F1E8] text-[#171717] border border-[#D6D2C8] rounded-sm text-[10px] text-center"
                  >
                    ▼ DOWN
                  </button>
                  <div />
                </div>

                <div className="flex items-center gap-1.5 pt-1">
                  <button
                    onClick={() => setPtzZoom((z) => Math.max(100, z - 20))}
                    className="flex-1 py-0.5 bg-[#FFFFFF] hover:bg-[#171717] hover:text-[#F4F1E8] text-[#171717] rounded-sm text-[10px] border border-[#D6D2C8] flex items-center justify-center gap-1"
                  >
                    <ZoomOut className="w-2.5 h-2.5" /> ZOOM -
                  </button>
                  <button
                    onClick={() => setPtzZoom((z) => Math.min(250, z + 20))}
                    className="flex-1 py-0.5 bg-[#FFFFFF] hover:bg-[#171717] hover:text-[#F4F1E8] text-[#171717] rounded-sm text-[10px] border border-[#D6D2C8] flex items-center justify-center gap-1"
                  >
                    <ZoomIn className="w-2.5 h-2.5" /> ZOOM +
                  </button>
                </div>
              </div>

              {/* AI Performance */}
              <div className="bg-[#F4F1E8] border border-[#D6D2C8] rounded-sm p-2.5 space-y-1 text-[10px]">
                <span className="font-bold text-[#171717] block uppercase">
                  AI LATENCY BREAKDOWN
                </span>
                <div className="grid grid-cols-2 gap-1 text-[#5E5E5E]">
                  <div>DETECTOR: <strong className="text-[#171717]">{cameraPerf?.detector_time_ms?.toFixed(1) || '12.4'}ms</strong></div>
                  <div>TRACKER: <strong className="text-[#171717]">{cameraPerf?.tracker_time_ms?.toFixed(1) || '3.1'}ms</strong></div>
                  <div>TOTAL: <strong className="text-[#1A5319]">{cameraPerf?.total_pipeline_ms?.toFixed(1) || '15.5'}ms</strong></div>
                  <div>FRAMES: <strong className="text-[#171717]">{selectedCam.total_frames_ingested || 0}</strong></div>
                </div>
              </div>

              {/* Tracks list */}
              <div className="space-y-1 text-xs">
                <span className="font-bold text-[#171717] uppercase text-[10px] block">
                  ACTIVE TRACKS ({cameraTracks.length})
                </span>
                <div className="max-h-44 overflow-y-auto space-y-1">
                  {cameraTracks.length === 0 ? (
                    <div className="p-3 bg-[#F4F1E8] rounded-sm text-center text-[#5E5E5E] text-[10px]">
                      No active tracks.
                    </div>
                  ) : (
                    cameraTracks.map((t) => (
                      <div
                        key={t.track_id}
                        className="p-1.5 bg-[#F4F1E8] rounded-sm border border-[#D6D2C8] flex items-center justify-between text-[10px]"
                      >
                        <span className="font-bold text-[#171717]">
                          #{t.track_id} ({t.object_type})
                        </span>
                        <span className="text-[#1A5319] font-bold">
                          {(t.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-6 text-center text-[#5E5E5E] text-xs">
              Select a camera to inspect telemetry.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
