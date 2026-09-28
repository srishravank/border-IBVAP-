import React, { useState, useEffect } from 'react';
import {
  X,
  ShieldCheck,
  Layers,
  CheckCircle2,
  FileCode,
  Check
} from 'lucide-react';
import { SecurityEvent, VerificationDetail } from '../types';
import { api } from '../services/api';

interface EventDetailModalProps {
  event: SecurityEvent | null;
  onClose: () => void;
  onAcknowledge: (id: string) => void;
}

export const EventDetailModal: React.FC<EventDetailModalProps> = ({
  event,
  onClose,
  onAcknowledge,
}) => {
  const [detail, setDetail] = useState<VerificationDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [viewJson, setViewJson] = useState<boolean>(false);

  useEffect(() => {
    if (!event) {
      setDetail(null);
      return;
    }

    let isMounted = true;
    setLoading(true);

    api.getEventVerification(event.event_id)
      .then((data) => {
        if (isMounted) setDetail(data);
      })
      .catch((err) => {
        console.error('Failed to load verification detail:', err);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [event]);

  if (!event) return null;

  const isAcknowledged = event.status === 'ACKNOWLEDGED' || !!event.acknowledged_at;
  const verDetail = detail || event.verification;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-forensic-surface border border-forensic-border rounded w-full max-w-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Modal Header */}
        <div className="p-4 bg-forensic-elevated border-b border-forensic-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-forensic-bg border border-forensic-border rounded text-forensic-text">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xs font-bold text-forensic-text uppercase tracking-widest font-mono">
                  SECURITY INCIDENT VERIFICATION AUDIT TRAIL
                </h2>
                <span className="px-2 py-0.5 bg-rose-500/10 text-[#FF4D4D] font-mono text-[10px] font-bold rounded border border-rose-500/30">
                  {event.event_type}
                </span>
              </div>
              <p className="text-xs text-forensic-muted font-mono">
                Event ID: {event.event_id}
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
          
          {/* Summary Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-forensic-surface border border-forensic-border rounded p-3">
              <span className="text-[10px] font-sans uppercase text-forensic-muted font-semibold block">CAMERA SOURCE</span>
              <span className="text-sm font-bold font-mono text-forensic-text">{event.camera_id}</span>
            </div>

            <div className="bg-forensic-surface border border-forensic-border rounded p-3">
              <span className="text-[10px] font-sans uppercase text-forensic-muted font-semibold block">VIRTUAL FENCE ZONE</span>
              <span className="text-sm font-bold font-mono text-forensic-text">{event.zone_name}</span>
            </div>

            <div className="bg-forensic-surface border border-forensic-border rounded p-3">
              <span className="text-[10px] font-sans uppercase text-forensic-muted font-semibold block">TRACK ID & CLASS</span>
              <span className="text-sm font-bold font-mono text-[#F5A623]">
                #{event.track_id} <span className="text-xs uppercase">({event.class_name || event.object_type})</span>
              </span>
            </div>

            <div className="bg-forensic-surface border border-forensic-border rounded p-3">
              <span className="text-[10px] font-sans uppercase text-forensic-muted font-semibold block">DETECTION CONFIDENCE</span>
              <span className="text-sm font-bold font-mono text-emerald-800 dark:text-[#C7FF3D]">
                {(event.confidence * 100).toFixed(1)}%
              </span>
            </div>
          </div>

          {/* Verification Pipeline Gate Summary */}
          <div className="bg-forensic-surface border border-forensic-border rounded p-4 space-y-3">
            <h3 className="text-xs font-bold text-forensic-text uppercase tracking-wider flex items-center gap-2 font-mono">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-[#C7FF3D]" />
              TEMPORAL VERIFICATION GATE & FALSE-POSITIVE SUPPRESSION AUDIT
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
              <div className="bg-forensic-bg p-2.5 rounded border border-forensic-border flex items-center justify-between">
                <span className="text-forensic-muted">Gate Requirement:</span>
                <span className="text-forensic-text font-semibold">
                  {verDetail?.required_frames || 3} Consecutive / Supporting Frames
                </span>
              </div>

              <div className="bg-forensic-bg p-2.5 rounded border border-forensic-border flex items-center justify-between">
                <span className="text-forensic-muted">Supporting Frames Captured:</span>
                <span className="text-emerald-800 dark:text-[#C7FF3D] font-bold">
                  {verDetail?.confirmed_frames || 3} Frames (PASS)
                </span>
              </div>

              <div className="bg-forensic-bg p-2.5 rounded border border-forensic-border flex items-center justify-between">
                <span className="text-forensic-muted">Ground Contact Point:</span>
                <span className="text-forensic-text font-semibold">
                  ({event.reference_point ? `${Math.round(event.reference_point[0])}, ${Math.round(event.reference_point[1])}` : 'N/A'})
                </span>
              </div>

              <div className="bg-forensic-bg p-2.5 rounded border border-forensic-border flex items-center justify-between">
                <span className="text-forensic-muted">Status Transition:</span>
                <span className="text-[#F5A623] font-semibold">
                  CANDIDATE → VERIFYING → CONFIRMED
                </span>
              </div>
            </div>
          </div>

          {/* Supporting Frame IDs list */}
          <div className="bg-forensic-surface border border-forensic-border rounded p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-forensic-text uppercase tracking-wider flex items-center gap-2 font-mono">
                <Layers className="w-4 h-4 text-forensic-muted" />
                SUPPORTING FRAME SEQUENCE (CHRONOLOGICAL)
              </h3>
              <span className="text-[11px] font-mono text-forensic-muted">
                {verDetail?.supporting_frame_ids?.length || 0} Frame IDs Recorded
              </span>
            </div>

            {loading ? (
              <div className="p-4 text-center text-xs font-mono text-forensic-muted animate-pulse">
                Loading verification frames...
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {(verDetail?.supporting_frame_ids || []).map((fid, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 bg-forensic-bg text-forensic-text border border-forensic-border rounded font-mono text-xs flex items-center gap-1.5"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-forensic-text" />
                    Frame #{fid}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Raw JSON View Option */}
          <div className="bg-forensic-surface border border-forensic-border rounded p-4 space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-forensic-text uppercase tracking-wider font-mono flex items-center gap-2">
                <FileCode className="w-4 h-4 text-forensic-muted" />
                SECURITY INCIDENT RAW JSON PAYLOAD (PHASE 4 READY)
              </h3>
              <button
                onClick={() => setViewJson(!viewJson)}
                className="text-xs font-mono text-forensic-text hover:underline"
              >
                {viewJson ? 'Hide JSON' : 'Show JSON'}
              </button>
            </div>

            {viewJson && (
              <pre className="p-3 bg-forensic-bg rounded text-[11px] font-mono text-forensic-text overflow-x-auto max-h-48 border border-forensic-border">
                {JSON.stringify(event, null, 2)}
              </pre>
            )}
          </div>

        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-forensic-elevated border-t border-forensic-border flex items-center justify-between">
          <div className="text-xs font-mono text-forensic-muted">
            {isAcknowledged ? (
              <span className="text-emerald-800 dark:text-[#C7FF3D] flex items-center gap-1 font-bold">
                <Check className="w-3.5 h-3.5" />
                Acknowledged ({event.acknowledged_at ? new Date(event.acknowledged_at).toLocaleTimeString() : 'Yes'})
              </span>
            ) : (
              <span className="text-[#FF4D4D] font-bold">UNACKNOWLEDGED SECURITY ALERT</span>
            )}
          </div>

          <div className="flex items-center gap-3">
            {!isAcknowledged && (
              <button
                onClick={() => {
                  onAcknowledge(event.event_id);
                  onClose();
                }}
                className="px-4 py-2 bg-[#FF4D4D] hover:bg-rose-600 text-white font-mono text-xs font-bold rounded shadow-sm transition flex items-center gap-1.5"
              >
                <Check className="w-4 h-4" />
                <span>Acknowledge Incident</span>
              </button>
            )}

            <button
              onClick={onClose}
              className="px-4 py-2 bg-forensic-surface hover:bg-forensic-bg text-forensic-text font-mono text-xs rounded border border-forensic-border transition"
            >
              Close
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};
