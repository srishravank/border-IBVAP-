import React, { useState, useEffect } from 'react';
import { Activity, AlertTriangle, CheckCircle, RotateCw, X, ShieldAlert, Trash2 } from 'lucide-react';
import { CameraEvent } from '../types';
import { api } from '../services/api';

interface CameraHealthEventsProps {
  events: CameraEvent[];
  selectedCameraId: string | null;
  onClose: () => void;
  onClearEvents: () => void;
}

export const CameraHealthEvents: React.FC<CameraHealthEventsProps> = ({
  events,
  selectedCameraId,
  onClose,
  onClearEvents,
}) => {
  const [filterCamera, setFilterCamera] = useState<string>(selectedCameraId || 'ALL');
  const [dbEvents, setDbEvents] = useState<CameraEvent[]>([]);
  const [loadingDb, setLoadingDb] = useState(false);

  useEffect(() => {
    if (selectedCameraId) {
      setFilterCamera(selectedCameraId);
      setLoadingDb(true);
      api.getCameraEvents(selectedCameraId, 40)
        .then((res) => setDbEvents(res))
        .catch((err) => console.error(err))
        .finally(() => setLoadingDb(false));
    }
  }, [selectedCameraId]);

  const displayEvents = selectedCameraId
    ? dbEvents
    : filterCamera === 'ALL'
    ? events
    : events.filter((e) => e.camera_id === filterCamera);

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'CAMERA_ONLINE':
        return <CheckCircle className="w-3.5 h-3.5 text-[#1A5319] shrink-0" />;
      case 'CAMERA_OFFLINE':
        return <AlertTriangle className="w-3.5 h-3.5 text-[#C53030] shrink-0" />;
      case 'CAMERA_RECONNECTING':
        return <RotateCw className="w-3.5 h-3.5 text-[#B45309] shrink-0" />;
      default:
        return <Activity className="w-3.5 h-3.5 text-[#5E5E5E] shrink-0" />;
    }
  };

  return (
    <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm flex flex-col h-full font-sans">
      {/* Header */}
      <div className="p-3 bg-[#ECE9E0] border-b border-[#D6D2C8] flex items-center justify-between font-mono">
        <div className="flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-[#171717]" />
          <span className="text-xs font-bold text-[#171717] uppercase">
            CAMERA TELEMETRY & HEALTH LOGS
          </span>
          {selectedCameraId && (
            <span className="px-1.5 py-0.2 bg-[#171717] text-[#C7FF3D] text-[9px] rounded-sm font-bold">
              {selectedCameraId}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          {!selectedCameraId && (
            <button
              onClick={onClearEvents}
              className="p-1 text-[#5E5E5E] hover:text-[#171717]"
              title="Clear Log"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          )}

          {selectedCameraId && (
            <button
              onClick={onClose}
              className="p-1 text-[#5E5E5E] hover:text-[#171717]"
              title="Close Filter"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Events List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1.5 max-h-[380px] divide-y divide-[#ECE9E0]">
        {loadingDb ? (
          <div className="p-6 text-center text-xs text-[#5E5E5E] font-mono">
            Loading telemetry logs...
          </div>
        ) : displayEvents.length === 0 ? (
          <div className="p-6 text-center text-xs text-[#5E5E5E] font-mono">
            No health events recorded.
          </div>
        ) : (
          displayEvents.map((evt, idx) => (
            <div
              key={idx}
              className="p-2 hover:bg-[#F4F1E8] rounded-sm text-[10px] font-mono transition"
            >
              <div className="flex items-center justify-between text-[#5E5E5E] mb-0.5">
                <span className="font-bold text-[#171717]">{evt.camera_id}</span>
                <span>{new Date(evt.timestamp).toLocaleTimeString()}</span>
              </div>
              <div className="flex items-start gap-1.5">
                {getEventIcon(evt.event_type)}
                <div>
                  <span className="font-bold text-[#171717] block">
                    {evt.event_type}
                  </span>
                  <p className="text-[#5E5E5E] text-[10px] mt-0.5">
                    {evt.message || 'Stream state transition'}
                  </p>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="p-2 bg-[#ECE9E0] border-t border-[#D6D2C8] text-[9px] font-mono text-[#5E5E5E] text-center">
        REAL-TIME SOC STREAM TELEMETRY ACTIVE
      </div>
    </div>
  );
};
