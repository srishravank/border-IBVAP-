import React from 'react';
import { Camera } from '../types';
import { CameraCard } from './CameraCard';

interface CameraGridProps {
  cameras: Camera[];
  onToggleIngestion: (id: string, currentlyEnabled: boolean) => void;
  onDelete: (id: string) => void;
  onSelectEvents: (id: string) => void;
  onInspectTracks: (id: string) => void;
  onConfigureZones: (camera: Camera) => void;
}

export const CameraGrid: React.FC<CameraGridProps> = ({
  cameras,
  onToggleIngestion,
  onDelete,
  onSelectEvents,
  onInspectTracks,
  onConfigureZones,
}) => {
  if (cameras.length === 0) {
    return (
      <div className="bg-[#111827] border border-[#1E293B] rounded-2xl p-12 text-center text-slate-400">
        <h3 className="text-base font-semibold text-slate-200 mb-1">No CCTV Cameras Registered</h3>
        <p className="text-xs text-slate-500 max-w-sm mx-auto mb-4">
          Register an RTSP camera stream, local video file, or development webcam to begin real-time border ingestion.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-2 2xl:grid-cols-4 gap-5">
      {cameras.map((cam) => (
        <CameraCard
          key={cam.camera_id}
          camera={cam}
          onToggleIngestion={onToggleIngestion}
          onDelete={onDelete}
          onSelectEvents={onSelectEvents}
          onInspectTracks={onInspectTracks}
          onConfigureZones={onConfigureZones}
        />
      ))}
    </div>
  );
};
