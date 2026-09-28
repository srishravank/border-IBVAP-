import React, { useState } from 'react';
import {
  ShieldAlert,
  CheckCircle,
  AlertTriangle,
  Clock,
  Check,
  ChevronRight,
  Activity
} from 'lucide-react';
import { SecurityEvent, CandidateSummary } from '../types';
import { api } from '../services/api';

interface SecurityEventsPanelProps {
  events: SecurityEvent[];
  candidates: CandidateSummary[];
  onSelectEvent: (event: SecurityEvent) => void;
  onRefresh: () => void;
}

export const SecurityEventsPanel: React.FC<SecurityEventsPanelProps> = ({
  events,
  candidates,
  onSelectEvent,
  onRefresh,
}) => {
  const [filterType, setFilterType] = useState<string>('ALL');
  const [acknowledgingId, setAcknowledgingId] = useState<string | null>(null);

  const handleAcknowledge = async (eventId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      setAcknowledgingId(eventId);
      await api.acknowledgeEvent(eventId, 'Operator (Console)');
      onRefresh();
    } catch (err) {
      console.error('Failed to acknowledge event:', err);
    } finally {
      setAcknowledgingId(null);
    }
  };

  const filteredEvents = events.filter((ev) => {
    if (filterType !== 'ALL' && ev.event_type !== filterType) return false;
    return true;
  });

  const getEventBadge = (type: string) => {
    switch (type) {
      case 'ZONE_INTRUSION':
        return (
          <span className="px-1.5 py-0.2 text-[9px] font-mono font-bold rounded-sm bg-[#FF4D4D] text-[#FFFFFF] flex items-center gap-1">
            <ShieldAlert className="w-2.5 h-2.5" />
            INTRUSION
          </span>
        );
      case 'ZONE_ENTRY':
        return (
          <span className="px-1.5 py-0.2 text-[9px] font-mono font-bold rounded-sm bg-[#F5A623] text-[#171717] flex items-center gap-1">
            <AlertTriangle className="w-2.5 h-2.5" />
            ZONE ENTRY
          </span>
        );
      case 'ZONE_EXIT':
        return (
          <span className="px-1.5 py-0.2 text-[9px] font-mono font-medium rounded-sm bg-[#ECE9E0] text-[#5E5E5E] border border-[#D6D2C8]">
            ZONE EXIT
          </span>
        );
      default:
        return (
          <span className="px-1.5 py-0.2 text-[9px] font-mono rounded-sm bg-[#ECE9E0] text-[#5E5E5E] border border-[#D6D2C8]">
            {type}
          </span>
        );
    }
  };

  return (
    <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm overflow-hidden flex flex-col h-full font-sans">
      {/* Header */}
      <div className="p-3 bg-[#ECE9E0] border-b border-[#D6D2C8] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 font-mono font-bold text-xs text-[#171717]">
            <ShieldAlert className="w-3.5 h-3.5 text-[#171717]" />
            <span>SECURITY EVENT STREAM</span>
            <span className="px-1.5 py-0.2 bg-[#171717] text-[#C7FF3D] text-[9px] rounded-sm">
              {events.length} CONFIRMED
            </span>
          </div>
        </div>

        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="px-2 py-0.5 bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm text-[10px] font-mono text-[#171717] focus:outline-none cursor-pointer"
        >
          <option value="ALL">ALL TYPES</option>
          <option value="ZONE_INTRUSION">INTRUSION</option>
          <option value="ZONE_ENTRY">ENTRY</option>
          <option value="ZONE_EXIT">EXIT</option>
        </select>
      </div>

      {/* Candidate Gate */}
      {candidates.length > 0 && (
        <div className="bg-[#F4F1E8] border-b border-[#D6D2C8] p-2.5">
          <div className="flex items-center justify-between mb-1.5 font-mono text-[9px]">
            <span className="font-bold text-[#171717] uppercase flex items-center gap-1">
              <Activity className="w-3 h-3 text-[#171717] animate-spin" />
              TEMPORAL VERIFICATION GATES ({candidates.length})
            </span>
            <span className="text-[#5E5E5E]">THRESHOLD: 3/5 FRAMES</span>
          </div>

          <div className="space-y-1.5">
            {candidates.map((c) => {
              const pct = Math.min(100, Math.round((c.confirmed_frames / (c.required_frames || 3)) * 100));
              return (
                <div
                  key={c.candidate_key}
                  className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-2 flex flex-col gap-1 text-[10px] font-mono"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[#171717]">
                      {c.camera_id} // TRACK #{c.track_id} ({c.object_type})
                    </span>
                    <span className="font-bold text-[#171717]">
                      {c.confirmed_frames}/{c.required_frames} FRAMES ({pct}%)
                    </span>
                  </div>

                  <div className="w-full bg-[#ECE9E0] h-1 rounded-none overflow-hidden">
                    <div
                      className="bg-[#171717] h-full transition-all duration-200"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Vertical Forensic Event Stream */}
      <div className="flex-1 overflow-y-auto max-h-[500px] divide-y divide-[#ECE9E0]">
        {filteredEvents.length === 0 ? (
          <div className="p-8 text-center text-[#5E5E5E] font-mono flex flex-col items-center justify-center">
            <CheckCircle className="w-6 h-6 text-[#8A877E] mb-1.5" />
            <p className="text-xs font-bold text-[#171717]">NO VERIFIED SECURITY INCIDENTS</p>
            <p className="text-[10px] text-[#8A877E] mt-0.5 max-w-xs">
              All active detections are outside restricted zones or filtered by false-positive suppression rules.
            </p>
          </div>
        ) : (
          filteredEvents.map((evt) => {
            const isAcknowledged = evt.status === 'ACKNOWLEDGED' || !!evt.acknowledged_at;
            return (
              <div
                key={evt.event_id}
                onClick={() => onSelectEvent(evt)}
                className="p-3 hover:bg-[#F4F1E8] cursor-pointer transition flex flex-col gap-1.5 font-mono text-[10px]"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    {getEventBadge(evt.event_type)}
                    <span className="font-bold text-[#171717]">{evt.camera_id}</span>
                    <span className="text-[#5E5E5E] font-semibold">{evt.zone_name}</span>
                  </div>

                  <span className="text-[#8A877E]">
                    {evt.created_at ? new Date(evt.created_at).toLocaleTimeString() : 'Live'}
                  </span>
                </div>

                <div className="flex items-center justify-between text-[#5E5E5E]">
                  <span>
                    TARGET: <strong className="text-[#171717]">{evt.class_name || evt.object_type}</strong> (#{evt.track_id})
                  </span>
                  <span>CONF: <strong className="text-[#1A5319]">{(evt.confidence * 100).toFixed(0)}%</strong></span>
                </div>

                <div className="flex items-center justify-between pt-1 border-t border-[#ECE9E0] text-[9px]">
                  <span className="text-[#8A877E]">
                    HASH: 9A71...C82F • BLOCK 0842
                  </span>

                  <div className="flex items-center gap-1.5">
                    {isAcknowledged ? (
                      <span className="text-[#1A5319] font-bold">● ACKNOWLEDGED</span>
                    ) : (
                      <button
                        onClick={(e) => handleAcknowledge(evt.event_id, e)}
                        disabled={acknowledgingId === evt.event_id}
                        className="px-1.5 py-0.2 bg-[#171717] hover:bg-[#292929] text-[#C7FF3D] rounded-sm font-bold transition"
                      >
                        {acknowledgingId === evt.event_id ? 'ACK...' : 'ACK'}
                      </button>
                    )}
                    <span className="text-[#171717] font-bold flex items-center">
                      INSPECT <ChevronRight className="w-3 h-3" />
                    </span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
