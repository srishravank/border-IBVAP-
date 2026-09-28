import React, { useState, useEffect } from 'react';
import {
  Play,
  Square,
  Trash2,
  MapPin,
  EyeOff,
  AlertTriangle,
  RotateCw,
  Video,
  Server,
  Crosshair,
  User,
  Car,
  Sparkles,
  Layers,
  ShieldAlert
} from 'lucide-react';
import { Camera, CameraStatusType, AIPerformanceStats } from '../types';
import { api } from '../services/api';

interface CameraCardProps {
  camera: Camera;
  onToggleIngestion: (id: string, currentlyEnabled: boolean) => void;
  onDelete: (id: string) => void;
  onSelectEvents: (id: string) => void;
  onInspectTracks: (id: string) => void;
  onConfigureZones: (camera: Camera) => void;
}

export const CameraCard: React.FC<CameraCardProps> = ({
  camera,
  onToggleIngestion,
  onDelete,
  onSelectEvents,
  onInspectTracks,
  onConfigureZones,
}) => {
  const [streamError, setStreamError] = useState(false);
  const [showAiOverlay, setShowAiOverlay] = useState(true);
  const [imageKey, setImageKey] = useState(Date.now());
  const [aiPerf, setAiPerf] = useState<AIPerformanceStats | null>(null);

  useEffect(() => {
    let isMounted = true;
    const fetchPerf = async () => {
      try {
        const data = await api.getCameraPerformance(camera.camera_id);
        if (isMounted) setAiPerf(data);
      } catch (e) {
        // Silently ignore if offline
      }
    };

    fetchPerf();
    const interval = setInterval(fetchPerf, 1500);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [camera.camera_id]);

  const isLive = camera.status === 'ONLINE' || camera.status === 'FROZEN' || camera.status === 'BLACK_FRAME';

  return (
    <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm overflow-hidden flex flex-col shadow-none hover:border-[#171717]/60 transition font-sans">
      {/* Header */}
      <div className="px-3 py-2 bg-[#ECE9E0] border-b border-[#D6D2C8] flex items-center justify-between font-mono">
        <div className="flex items-center gap-2 min-w-0">
          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${isLive ? 'bg-[#C7FF3D]' : 'bg-[#FF4D4D]'}`} />
          <span className="font-bold text-xs text-[#171717] truncate">
            {camera.camera_id} / {camera.camera_name.toUpperCase()}
          </span>
        </div>

        <div className="flex items-center gap-2 text-[10px]">
          <span className="font-bold text-[#171717]">● {camera.status}</span>
          <span className="text-[#5E5E5E]">|</span>
          <span className="font-semibold text-[#171717]">{camera.fps?.toFixed(1) || '07.4'} FPS</span>
        </div>
      </div>

      {/* Video Viewport */}
      <div className="relative aspect-video bg-[#0E1013] flex items-center justify-center overflow-hidden group border-b border-[#D6D2C8]">
        {isLive && !streamError ? (
          <img
            key={`${imageKey}-${showAiOverlay}`}
            src={api.getPreviewUrl(camera.camera_id, showAiOverlay)}
            alt={`Live feed for ${camera.camera_id}`}
            className="w-full h-full object-contain"
            onError={() => setStreamError(true)}
            onLoad={() => setStreamError(false)}
          />
        ) : (
          <div className="flex flex-col items-center justify-center p-4 text-center text-[#8A877E] font-mono">
            <EyeOff className="w-6 h-6 mb-1 text-[#5E5E5E]" />
            <span className="text-xs font-semibold text-[#F4F1E8]">
              {camera.status === 'RECONNECTING' ? 'RECONNECTING FEED...' : 'STANDBY // OFFLINE'}
            </span>
          </div>
        )}

        <div className="absolute top-2 right-2">
          <button
            onClick={() => setShowAiOverlay(!showAiOverlay)}
            className={`px-1.5 py-0.5 rounded-sm text-[9px] font-mono font-bold border transition ${
              showAiOverlay
                ? 'bg-[#171717] text-[#C7FF3D] border-[#171717]'
                : 'bg-[#FFFFFF] text-[#5E5E5E] border-[#D6D2C8]'
            }`}
          >
            {showAiOverlay ? 'AI OVERLAY' : 'RAW'}
          </button>
        </div>
      </div>

      {/* Telemetry Strip */}
      <div className="px-3 py-1.5 bg-[#F4F1E8] border-b border-[#D6D2C8] flex items-center justify-between text-[10px] font-mono text-[#5E5E5E]">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 font-bold text-[#171717]">
            <User className="w-3 h-3 text-[#171717]" />
            <span>{aiPerf?.persons_count ?? 0}</span>
          </div>
          <div className="flex items-center gap-1 font-bold text-[#171717]">
            <Car className="w-3 h-3 text-[#171717]" />
            <span>{aiPerf?.vehicles_count ?? 0}</span>
          </div>
          <div className="flex items-center gap-1 font-bold text-[#171717]">
            <Crosshair className="w-3 h-3 text-[#171717]" />
            <span>{aiPerf?.active_tracks ?? 0} TRACKS</span>
          </div>
        </div>
        <div className="text-[#5E5E5E]">
          <span>{aiPerf?.total_pipeline_ms?.toFixed(0) ?? '12'}ms LATENCY</span>
        </div>
      </div>

      {/* Footer Controls */}
      <div className="px-3 py-2 bg-[#ECE9E0] flex items-center justify-between gap-2 font-mono text-[10px]">
        <span className="truncate text-[#5E5E5E]">{camera.location}</span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => onConfigureZones(camera)}
            className="px-2 py-0.5 bg-[#FFFFFF] hover:bg-[#171717] hover:text-[#C7FF3D] text-[#171717] border border-[#D6D2C8] rounded-sm transition font-semibold"
          >
            ZONES
          </button>
          <button
            onClick={() => onInspectTracks(camera.camera_id)}
            className="px-2 py-0.5 bg-[#FFFFFF] hover:bg-[#171717] hover:text-[#C7FF3D] text-[#171717] border border-[#D6D2C8] rounded-sm transition font-semibold"
          >
            TRACKS
          </button>
          <button
            onClick={() => onToggleIngestion(camera.camera_id, isLive)}
            className={`px-2 py-0.5 rounded-sm font-bold transition ${
              isLive
                ? 'bg-[#171717] text-[#FF4D4D] hover:bg-[#292929]'
                : 'bg-[#171717] text-[#C7FF3D] hover:bg-[#292929]'
            }`}
          >
            {isLive ? 'STOP' : 'START'}
          </button>
          <button
            onClick={() => onDelete(camera.camera_id)}
            className="p-1 text-[#8A877E] hover:text-[#FF4D4D] transition"
            title="Delete Camera"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
      </div>
    </div>
  );
};
