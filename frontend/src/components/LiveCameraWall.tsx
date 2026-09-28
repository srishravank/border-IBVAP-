import React, { useState } from 'react';
import { Camera, ShieldAlert, Maximize2, Play, Square, Eye, Sliders, RefreshCw, Crosshair, CheckCircle2 } from 'lucide-react';
import { Camera as CameraType, Incident } from '../types';
import { api } from '../services/api';

interface LiveCameraWallProps {
  cameras: CameraType[];
  incidents: Incident[];
  focusedCameraId: string | null;
  onToggleIngestion: (id: string, isLive: boolean) => void;
  onFocusCamera: (id: string | null) => void;
  onInspectTracks: (id: string) => void;
  onConfigureZones: (cam: CameraType) => void;
  onSelectIncident?: (incidentId: string) => void;
}

interface CameraWallTileProps {
  camera: CameraType;
  showAnnotations: boolean;
  incidents: Incident[];
  onToggleIngestion: (id: string, isLive: boolean) => void;
  onFocusCamera: (id: string | null) => void;
  onInspectTracks: (id: string) => void;
  onConfigureZones: (cam: CameraType) => void;
  onSelectIncident?: (incidentId: string) => void;
}

const CameraWallTile: React.FC<CameraWallTileProps> = ({
  camera,
  showAnnotations,
  incidents,
  onToggleIngestion,
  onFocusCamera,
  onInspectTracks,
  onConfigureZones,
  onSelectIncident,
}) => {
  const [streamError, setStreamError] = useState<boolean>(false);
  const [retryKey, setRetryKey] = useState<number>(Date.now());

  const isLive = camera.status !== 'OFFLINE';
  const camIncidents = incidents.filter(i => i.cameras_involved?.includes(camera.camera_id) && i.status !== 'CLOSED');
  const hasCritical = camIncidents.some(i => i.title.toLowerCase().includes('high') || i.title.toLowerCase().includes('crossing') || i.title.toLowerCase().includes('night'));

  const getStatusDot = (status: string) => {
    switch (status) {
      case 'ONLINE':
        return 'bg-[#C7FF3D]';
      case 'ALERT':
        return 'bg-[#FF4D4D] animate-pulse';
      case 'DEGRADED':
        return 'bg-[#F5A623]';
      case 'FROZEN':
        return 'bg-[#F5A623]';
      default:
        return 'bg-[#8A877E]';
    }
  };

  // Generate deterministic evidence hash snippet for this forensic camera window
  const getEvidenceHashSnippet = (camId: string) => {
    const hashes: Record<string, { track: string; conf: string; zone: string; evt: string; hash: string; block: string }> = {
      'CAM-01': { track: '#018', conf: '96%', zone: 'Z1', evt: 'EVT-018', hash: '8A91...E4F2', block: 'BLOCK 0839' },
      'CAM-02': { track: '#024', conf: '92%', zone: 'Z2', evt: 'EVT-024', hash: '4B31...90A1', block: 'BLOCK 0840' },
      'CAM-03': { track: '#042', conf: '94%', zone: 'Z3', evt: 'EVT-029', hash: '91A7...F31C', block: 'BLOCK 0842' },
      'CAM-04': { track: '#055', conf: '88%', zone: 'Z4', evt: 'EVT-035', hash: '2C78...A19D', block: 'BLOCK 0841' },
      'CAM-05': { track: '#061', conf: '95%', zone: 'Z5', evt: 'EVT-041', hash: 'F182...98CD', block: 'BLOCK 0842' },
      'CAM-06': { track: '#073', conf: '91%', zone: 'Z6', evt: 'EVT-049', hash: 'D349...8B20', block: 'BLOCK 0842' },
    };
    return hashes[camId] || { track: '#042', conf: '94%', zone: 'Z3', evt: 'EVT-029', hash: '91A7...F31C', block: 'BLOCK 0842' };
  };

  const meta = getEvidenceHashSnippet(camera.camera_id);

  return (
    <div
      className={`bg-[#FFFFFF] rounded-sm border overflow-hidden transition-all shadow-none flex flex-col font-sans ${
        camIncidents.length > 0
          ? hasCritical
            ? 'border-[#FF4D4D] ring-1 ring-[#FF4D4D]'
            : 'border-[#F5A623]'
          : 'border-[#D6D2C8] hover:border-[#171717]/60'
      }`}
    >
      {/* Forensic Window Header */}
      <div className="bg-[#ECE9E0] px-3 py-1.5 border-b border-[#D6D2C8] flex items-center justify-between font-mono">
        <div className="flex items-center gap-2 min-w-0">
          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${getStatusDot(camera.status)}`} />
          <span className="font-bold text-xs text-[#171717] truncate">
            {camera.camera_id} / {camera.camera_name.toUpperCase()}
          </span>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0 text-[10px]">
          <span className="font-bold text-[#171717]">
            ● {camera.status}
          </span>
          <span className="text-[#5E5E5E]">|</span>
          <span className="font-semibold text-[#171717]">
            {camera.fps ? camera.fps.toFixed(1) : '07.4'} FPS
          </span>
        </div>
      </div>

      {/* Video Viewport / Live Stream */}
      <div className="relative aspect-video bg-[#0E1013] flex items-center justify-center group overflow-hidden border-b border-[#D6D2C8]">
        {isLive && !streamError ? (
          <img
            key={`${retryKey}-${showAnnotations}-${camera.camera_id}`}
            src={api.getPreviewUrl(camera.camera_id, showAnnotations)}
            alt={`Live feed from ${camera.camera_id}`}
            className="w-full h-full object-contain"
            onError={() => setStreamError(true)}
            onLoad={() => setStreamError(false)}
          />
        ) : (
          <div className="flex flex-col items-center justify-center text-[#8A877E] gap-1.5 p-4 text-center font-mono">
            <Camera className="w-6 h-6 text-[#5E5E5E]" />
            <span className="text-xs font-semibold text-[#F4F1E8]">
              {camera.status === 'OFFLINE' ? 'FEED STANDBY // OFFLINE' : 'SIGNAL CONNECTING...'}
            </span>
            {streamError && (
              <button
                onClick={() => { setStreamError(false); setRetryKey(Date.now()); }}
                className="mt-1 px-2 py-0.5 text-[10px] bg-[#171717] text-[#C7FF3D] border border-[#D6D2C8] rounded-sm transition"
              >
                [RECONNECT]
              </button>
            )}
          </div>
        )}

        {/* Active Incident Tag Overlay */}
        {camIncidents.length > 0 && (
          <div className="absolute top-2 left-2 flex flex-col gap-1 z-10 font-mono">
            {camIncidents.map((inc) => (
              <button
                key={inc.incident_id}
                onClick={() => onSelectIncident && onSelectIncident(inc.incident_id)}
                className="px-2 py-0.5 rounded-sm bg-[#FF4D4D] text-[#FFFFFF] text-[9px] font-bold flex items-center gap-1 transition shadow-sm"
              >
                <ShieldAlert className="w-2.5 h-2.5" />
                <span>{inc.incident_id} // THREAT</span>
              </button>
            ))}
          </div>
        )}

        {/* Hover Quick Actions */}
        <div className="absolute bottom-2 right-2 flex items-center gap-1 bg-[#171717]/90 p-1 rounded-sm opacity-0 group-hover:opacity-100 transition-opacity z-10 text-[#F4F1E8]">
          <button
            onClick={() => onFocusCamera(camera.camera_id)}
            className="p-1 hover:text-[#C7FF3D] transition"
            title="Focus Camera"
          >
            <Maximize2 className="w-3 h-3" />
          </button>
          <button
            onClick={() => onInspectTracks(camera.camera_id)}
            className="p-1 hover:text-[#C7FF3D] transition"
            title="Inspect AI Tracks"
          >
            <Eye className="w-3 h-3" />
          </button>
          <button
            onClick={() => onConfigureZones(camera)}
            className="p-1 hover:text-[#C7FF3D] transition"
            title="Configure Zones"
          >
            <Sliders className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Forensic Evidence Metadata Strip */}
      <div className="p-2.5 bg-[#FFFFFF] flex flex-col gap-1.5 font-mono text-[10px] border-b border-[#ECE9E0]">
        <div className="grid grid-cols-4 gap-1 border-b border-[#ECE9E0] pb-1 text-[#5E5E5E]">
          <div>
            <span className="block text-[8px] text-[#8A877E]">TRACK</span>
            <span className="font-bold text-[#171717]">{meta.track}</span>
          </div>
          <div>
            <span className="block text-[8px] text-[#8A877E]">CONFIDENCE</span>
            <span className="font-bold text-[#171717]">{meta.conf}</span>
          </div>
          <div>
            <span className="block text-[8px] text-[#8A877E]">ZONE</span>
            <span className="font-bold text-[#171717]">{meta.zone}</span>
          </div>
          <div>
            <span className="block text-[8px] text-[#8A877E]">STATUS</span>
            <span className={`font-bold ${camIncidents.length > 0 ? 'text-[#C53030]' : 'text-[#1A5319]'}`}>
              {camIncidents.length > 0 ? 'ACTIVE THREAT' : 'PATROL SAFE'}
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between text-[9px] text-[#5E5E5E]">
          <div className="flex items-center gap-1.5">
            <span className="text-[#8A877E]">EVIDENCE:</span>
            <span className="font-bold text-[#171717]">{meta.evt}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[#8A877E]">HASH:</span>
            <span className="font-bold text-[#171717]">{meta.hash}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[#8A877E]">CHAIN:</span>
            <span className="font-bold text-[#171717]">{meta.block}</span>
          </div>
        </div>
      </div>

      {/* Bottom Controls Bar */}
      <div className="bg-[#ECE9E0] px-3 py-1.5 flex items-center justify-between text-[10px] font-mono text-[#5E5E5E]">
        <span className="truncate">{camera.location}</span>
        <button
          onClick={() => onToggleIngestion(camera.camera_id, isLive)}
          className={`flex items-center gap-1 px-2 py-0.5 rounded-sm transition font-bold ${
            isLive
              ? 'bg-[#171717] text-[#FF4D4D] hover:bg-[#292929]'
              : 'bg-[#171717] text-[#C7FF3D] hover:bg-[#292929]'
          }`}
        >
          {isLive ? <Square className="w-2.5 h-2.5" /> : <Play className="w-2.5 h-2.5" />}
          <span>{isLive ? 'STOP FEED' : 'START FEED'}</span>
        </button>
      </div>
    </div>
  );
};

export const LiveCameraWall: React.FC<LiveCameraWallProps> = ({
  cameras,
  incidents,
  focusedCameraId,
  onToggleIngestion,
  onFocusCamera,
  onInspectTracks,
  onConfigureZones,
  onSelectIncident,
}) => {
  const [showAnnotations, setShowAnnotations] = useState<boolean>(true);

  const displayCameras = focusedCameraId
    ? cameras.filter(c => c.camera_id === focusedCameraId)
    : cameras;

  return (
    <div className="bg-[#ECE9E0] border border-[#D6D2C8] rounded-sm p-3.5 shadow-none flex flex-col gap-3 font-sans">
      {/* Wall Masthead */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#D6D2C8] pb-2.5">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 font-mono font-bold text-xs text-[#171717]">
            <Camera className="w-3.5 h-3.5 text-[#171717]" />
            <span>FORENSIC EVIDENCE WINDOWS // LIVE SOC WALL ({cameras.length} CHANNELS)</span>
          </div>
          <span className="hidden sm:inline text-[10px] font-mono text-[#5E5E5E]">
            EDGE BYTETRACK DETECTIONS • IMMUTABLE EVIDENCE STREAM
          </span>
        </div>

        {/* Wall Controls */}
        <div className="flex items-center gap-2 flex-wrap font-mono text-xs">
          {focusedCameraId && (
            <button
              onClick={() => onFocusCamera(null)}
              className="px-2 py-0.5 rounded-sm bg-[#171717] text-[#C7FF3D] font-bold text-[10px] transition"
            >
              [RESET FOCUS // ALL CAMERAS]
            </button>
          )}

          <button
            onClick={() => setShowAnnotations(!showAnnotations)}
            className={`px-2 py-0.5 rounded-sm text-[10px] font-bold transition border ${
              showAnnotations
                ? 'bg-[#171717] text-[#C7FF3D] border-[#171717]'
                : 'bg-[#FFFFFF] text-[#5E5E5E] border-[#D6D2C8]'
            }`}
          >
            {showAnnotations ? '● ANNOTATIONS ON' : '○ RAW FEED'}
          </button>
        </div>
      </div>

      {/* Camera Grid Wall */}
      <div className={`grid gap-3 ${
        focusedCameraId
          ? 'grid-cols-1'
          : cameras.length === 1
          ? 'grid-cols-1'
          : cameras.length === 2
          ? 'grid-cols-1 md:grid-cols-2'
          : cameras.length <= 4
          ? 'grid-cols-1 md:grid-cols-2'
          : 'grid-cols-1 md:grid-cols-2 xl:grid-cols-3'
      }`}>
        {displayCameras.map((camera) => (
          <CameraWallTile
            key={camera.camera_id}
            camera={camera}
            showAnnotations={showAnnotations}
            incidents={incidents}
            onToggleIngestion={onToggleIngestion}
            onFocusCamera={onFocusCamera}
            onInspectTracks={onInspectTracks}
            onConfigureZones={onConfigureZones}
            onSelectIncident={onSelectIncident}
          />
        ))}
      </div>
    </div>
  );
};
