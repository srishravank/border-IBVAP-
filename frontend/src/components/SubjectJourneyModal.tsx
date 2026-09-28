import React, { useState, useEffect } from 'react';
import {
  X,
  Compass,
  ArrowRight,
  Clock,
  MapPin,
  Crosshair,
  ShieldAlert,
  Car,
  CheckCircle2,
  Layers,
  ChevronRight,
  Sparkles
} from 'lucide-react';
import { SubjectJourney, SubjectJourneyStep } from '../types';
import { api } from '../services/api';

interface SubjectJourneyModalProps {
  subjectId: string | null;
  onClose: () => void;
}

export const SubjectJourneyModal: React.FC<SubjectJourneyModalProps> = ({
  subjectId,
  onClose,
}) => {
  const [journey, setJourney] = useState<SubjectJourney | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedStep, setSelectedStep] = useState<number | null>(null);

  useEffect(() => {
    if (!subjectId) {
      setJourney(null);
      return;
    }

    let isMounted = true;
    setLoading(true);

    api.getSubjectJourney(subjectId)
      .then((data) => {
        if (isMounted) {
          setJourney(data);
          if (data.journey_steps.length > 0) {
            setSelectedStep(data.journey_steps[0].sequence);
          }
        }
      })
      .catch((err) => {
        console.error('Failed to load subject journey:', err);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [subjectId]);

  if (!subjectId) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-forensic-surface border border-forensic-border rounded w-full max-w-4xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Modal Header */}
        <div className="p-4 bg-forensic-elevated border-b border-forensic-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-forensic-bg border border-forensic-border rounded text-forensic-text">
              <Compass className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xs font-bold text-forensic-text uppercase tracking-widest font-mono">
                  CROSS-CAMERA SUBJECT JOURNEY RECONSTRUCTION
                </h2>
                <span className="px-2 py-0.5 bg-forensic-bg text-forensic-text font-mono text-[10px] rounded border border-forensic-border">
                  {subjectId}
                </span>
              </div>
              <p className="text-xs text-forensic-muted font-mono">
                Multi-camera route progression, local track links & evidence verification
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
          
          {loading ? (
            <div className="p-12 text-center text-xs font-mono text-forensic-muted animate-pulse flex flex-col items-center gap-2">
              <Compass className="w-6 h-6 animate-spin text-forensic-text" />
              <span>Reconstructing multi-camera journey path...</span>
            </div>
          ) : !journey ? (
            <div className="p-12 text-center text-xs font-mono text-forensic-muted">
              No journey records found for subject {subjectId}.
            </div>
          ) : (
            <>
              {/* Journey Overview Bar */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-forensic-surface border border-forensic-border rounded p-3">
                  <span className="text-[10px] font-sans uppercase text-forensic-muted font-semibold block">GLOBAL SUBJECT</span>
                  <span className="text-sm font-bold font-mono text-forensic-text">{journey.subject_id}</span>
                </div>

                <div className="bg-forensic-surface border border-forensic-border rounded p-3">
                  <span className="text-[10px] font-sans uppercase text-forensic-muted font-semibold block">TARGET TYPE</span>
                  <span className="text-sm font-bold font-mono text-forensic-text uppercase">{journey.object_type}</span>
                </div>

                <div className="bg-forensic-surface border border-forensic-border rounded p-3">
                  <span className="text-[10px] font-sans uppercase text-forensic-muted font-semibold block">CAMERAS VISITED</span>
                  <span className="text-sm font-bold font-mono text-forensic-text">
                    {journey.total_cameras} Sensors ({journey.cameras_sequence.join(' → ')})
                  </span>
                </div>

                <div className="bg-forensic-surface border border-forensic-border rounded p-3">
                  <span className="text-[10px] font-sans uppercase text-forensic-muted font-semibold block">TRACK DURATION</span>
                  <span className="text-sm font-bold font-mono text-emerald-800 dark:text-[#C7FF3D]">
                    {new Date(journey.first_seen).toLocaleTimeString()} - {new Date(journey.last_seen).toLocaleTimeString()}
                  </span>
                </div>
              </div>

              {/* Visual Breadcrumb Camera Path */}
              <div className="bg-forensic-surface border border-forensic-border rounded p-4">
                <h3 className="text-xs font-bold text-forensic-text uppercase tracking-wider font-mono mb-3 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-forensic-muted" />
                  CAMERA SENSOR ROUTE PROGRESSION
                </h3>

                <div className="flex items-center gap-2 overflow-x-auto pb-2">
                  {journey.journey_steps.map((step, idx) => (
                    <React.Fragment key={step.sequence}>
                      <button
                        onClick={() => setSelectedStep(step.sequence)}
                        className={`px-3 py-2 rounded text-xs font-mono border transition flex items-center gap-2 shrink-0 ${
                          selectedStep === step.sequence
                            ? 'bg-forensic-elevated border-forensic-text text-forensic-text shadow-sm'
                            : 'bg-forensic-bg border-forensic-border text-forensic-muted hover:text-forensic-text'
                        }`}
                      >
                        <span className="w-5 h-5 rounded-full bg-forensic-elevated text-forensic-text border border-forensic-border flex items-center justify-center text-[10px] font-bold">
                          {step.sequence}
                        </span>
                        <div className="text-left">
                          <span className="font-bold block">{step.camera_id}</span>
                          <span className="text-[10px] text-forensic-muted block">{step.formatted_track_id}</span>
                        </div>
                      </button>

                      {idx < journey.journey_steps.length - 1 && (
                        <ArrowRight className="w-4 h-4 text-forensic-muted shrink-0" />
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>

              {/* Selected Step Detailed Cards */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold text-forensic-text uppercase tracking-wider font-mono flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-[#F5A623]" />
                  STEP-BY-STEP CROSS-CAMERA EVIDENCE & EVENT LOG
                </h3>

                {journey.journey_steps.map((step) => {
                  const isSelected = selectedStep === step.sequence;
                  return (
                    <div
                      key={step.sequence}
                      onClick={() => setSelectedStep(step.sequence)}
                      className={`p-4 rounded border transition cursor-pointer ${
                        isSelected
                          ? 'bg-forensic-surface border-forensic-text shadow-md'
                          : 'bg-forensic-surface/60 border-forensic-border hover:bg-forensic-surface'
                      }`}
                    >
                      {/* Step Header */}
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-forensic-border pb-3 mb-3">
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 bg-forensic-bg text-forensic-text font-mono text-xs font-bold rounded border border-forensic-border">
                            STEP #{step.sequence}
                          </span>
                          <span className="text-sm font-bold text-forensic-text font-mono">
                            {step.camera_id} — {step.camera_name}
                          </span>
                          <span className="px-2 py-0.5 bg-forensic-bg text-forensic-muted font-mono text-xs rounded border border-forensic-border">
                            Local Track: #{step.track_id} ({step.formatted_track_id})
                          </span>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 text-xs font-mono font-bold rounded border ${
                            step.match_score >= 0.80
                              ? 'bg-[#C7FF3D]/10 text-emerald-800 dark:text-[#C7FF3D] border-emerald-500/40'
                              : 'bg-forensic-bg text-forensic-text border-forensic-border'
                          }`}>
                            Match Confidence: {(step.match_score * 100).toFixed(0)}% ({step.match_status})
                          </span>
                        </div>
                      </div>

                      {/* Evidence Factors */}
                      <div className="space-y-2 mb-3">
                        <span className="text-[10px] font-mono text-forensic-muted uppercase font-semibold block">
                          EVIDENCE & MATCH FACTORS:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {step.evidence.map((factor, fIdx) => (
                            <span
                              key={fIdx}
                              className="px-2 py-1 bg-forensic-bg text-forensic-text border border-forensic-border rounded text-xs font-mono flex items-center gap-1"
                            >
                              <CheckCircle2 className="w-3 h-3 text-emerald-600 dark:text-[#C7FF3D]" />
                              <span>{factor}</span>
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Triggered Phase 3 Events */}
                      {step.events_triggered.length > 0 && (
                        <div className="space-y-2 mb-3 bg-rose-500/10 border border-rose-500/30 rounded p-2.5">
                          <span className="text-[10px] font-mono text-[#FF4D4D] uppercase font-bold flex items-center gap-1">
                            <ShieldAlert className="w-3.5 h-3.5 text-[#FF4D4D]" />
                            CONFIRMED SECURITY INCIDENTS IN ZONE ({step.events_triggered.length})
                          </span>
                          <div className="space-y-1">
                            {step.events_triggered.map((ev, eIdx) => (
                              <div key={eIdx} className="flex items-center justify-between text-xs font-mono">
                                <span className="text-forensic-text font-semibold">
                                  {ev.event_type} in &quot;{ev.zone_name}&quot;
                                </span>
                                <span className="text-forensic-muted text-[11px]">
                                  {new Date(ev.timestamp).toLocaleTimeString()} (Conf: {(ev.confidence * 100).toFixed(0)}%)
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Associated Vehicles */}
                      {step.associated_vehicles.length > 0 && (
                        <div className="space-y-1.5 bg-amber-500/10 border border-amber-500/30 rounded p-2.5">
                          <span className="text-[10px] font-mono text-[#F5A623] uppercase font-bold flex items-center gap-1">
                            <Car className="w-3.5 h-3.5 text-[#F5A623]" />
                            CONTEXTUALLY ASSOCIATED VEHICLE ACTIVITY
                          </span>
                          {step.associated_vehicles.map((veh, vIdx) => (
                            <div key={vIdx} className="text-xs font-mono text-forensic-text flex items-center justify-between">
                              <span>Linked Vehicle: <strong className="text-[#F5A623]">{veh.vehicle_id}</strong> ({veh.proximity_meters}m proximity)</span>
                              <span className="text-forensic-muted text-[11px]">{veh.notes}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Timestamps Footer */}
                      <div className="pt-2 border-t border-forensic-border flex items-center justify-between text-[11px] font-mono text-forensic-muted">
                        <span>First Seen: {new Date(step.first_seen).toLocaleTimeString()}</span>
                        <span>Last Seen: {new Date(step.last_seen).toLocaleTimeString()}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}

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
