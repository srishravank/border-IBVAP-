import React, { useState, useEffect } from 'react';
import {
  Incident,
  IncidentLifecycle,
  IncidentNarrative,
  RecommendedCameraResponse,
  IncidentNote,
  OperatorAction,
  UserRole,
  ConnectivityStatus,
  SyncQueueSummary,
} from '../types';
import { api } from '../services/api';
import {
  ShieldAlert,
  CheckCircle2,
  Search,
  Eye,
  UserCheck,
  FileText,
  Compass,
  MessageSquare,
  Send,
  Lock,
  Maximize2,
} from 'lucide-react';
import { ConnectionStatus } from '../components/Sync/ConnectionStatus';
import { OfflineBanner } from '../components/Sync/OfflineBanner';
import { SyncStatusDrawer } from '../components/Sync/SyncStatusDrawer';

interface IncidentCommandViewProps {
  incidents: Incident[];
  currentRole: UserRole;
  currentOperatorId: string;
  onSelectIncidentModal: (incidentId: string) => void;
  onFocusCamera: (cameraId: string | null) => void;
  onRefresh: () => void;
}

export const IncidentCommandView: React.FC<IncidentCommandViewProps> = ({
  incidents,
  currentRole,
  currentOperatorId,
  onSelectIncidentModal,
  onFocusCamera,
  onRefresh,
}) => {
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>(
    incidents.length > 0 ? incidents[0].incident_id : ''
  );
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const [lifecycle, setLifecycle] = useState<IncidentLifecycle | null>(null);
  const [narrative, setNarrative] = useState<IncidentNarrative | null>(null);
  const [recommendedCams, setRecommendedCams] = useState<RecommendedCameraResponse | null>(null);
  const [notes, setNotes] = useState<IncidentNote[]>([]);
  const [actions, setActions] = useState<OperatorAction[]>([]);
  const [newNote, setNewNote] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const [connectivity, setConnectivity] = useState<ConnectivityStatus | null>(null);
  const [syncSummary, setSyncSummary] = useState<SyncQueueSummary | null>(null);
  const [isSyncDrawerOpen, setIsSyncDrawerOpen] = useState<boolean>(false);
  const [isTogglingConnectivity, setIsTogglingConnectivity] = useState<boolean>(false);

  const fetchConnectivityAndSync = async () => {
    try {
      const [conn, sync] = await Promise.all([
        api.getConnectivityStatus().catch(() => null),
        api.getSyncStatus().catch(() => null),
      ]);
      if (conn) setConnectivity(conn);
      if (sync?.summary) setSyncSummary(sync.summary);
    } catch (err) {
      console.error('Failed to load connectivity / sync status', err);
    }
  };

  useEffect(() => {
    fetchConnectivityAndSync();
    const interval = setInterval(fetchConnectivityAndSync, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleToggleConnectivity = async () => {
    try {
      setIsTogglingConnectivity(true);
      const isCurrentlyOffline = connectivity?.state === 'OFFLINE' || connectivity?.state === 'DEGRADED';
      const targetState = isCurrentlyOffline ? 'ONLINE' : 'OFFLINE';
      const res = await api.simulateConnectivity(targetState, `Operator toggled to ${targetState}`);
      setConnectivity(res);
      await fetchConnectivityAndSync();
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Failed to toggle connectivity state');
    } finally {
      setIsTogglingConnectivity(false);
    }
  };

  const filteredIncidents = incidents.filter((inc) => {
    if (filterStatus !== 'ALL') {
      if (filterStatus === 'ACTIVE' && inc.status === 'CLOSED') return false;
      if (filterStatus !== 'ACTIVE' && inc.status !== filterStatus) return false;
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const mId = inc.incident_id.toLowerCase().includes(q);
      const mSubj = inc.subject_id.toLowerCase().includes(q);
      const mTitle = inc.title.toLowerCase().includes(q);
      if (!mId && !mSubj && !mTitle) return false;
    }
    return true;
  });

  useEffect(() => {
    if (!selectedIncidentId) {
      if (incidents.length > 0) setSelectedIncidentId(incidents[0].incident_id);
      return;
    }

    let isMounted = true;
    const loadData = async () => {
      try {
        const [life, narr, recs, nts, acts] = await Promise.all([
          api.getIncidentLifecycle(selectedIncidentId).catch(() => null),
          api.getIncidentNarrative(selectedIncidentId).catch(() => null),
          api.getRecommendedCameras(selectedIncidentId).catch(() => null),
          api.getIncidentNotes(selectedIncidentId).catch(() => []),
          api.getOperatorActions(selectedIncidentId, 20).catch(() => []),
        ]);
        if (isMounted) {
          setLifecycle(life);
          setNarrative(narr);
          setRecommendedCams(recs);
          setNotes(nts);
          setActions(acts);
        }
      } catch (e) {
        console.error(e);
      }
    };
    loadData();

    return () => {
      isMounted = false;
    };
  }, [selectedIncidentId, incidents]);

  const handleTransition = async (targetState: 'ACKNOWLEDGED' | 'INVESTIGATING' | 'CLOSED') => {
    if (!selectedIncidentId) return;
    try {
      setIsSubmitting(true);
      if (targetState === 'ACKNOWLEDGED') {
        await api.acknowledgeIncident(selectedIncidentId, currentOperatorId, currentRole, 'Acknowledged in command center');
      } else if (targetState === 'INVESTIGATING') {
        await api.investigateIncident(selectedIncidentId, currentOperatorId, currentRole, 'Investigation launched in command center');
      } else if (targetState === 'CLOSED') {
        await api.closeIncident(selectedIncidentId, currentOperatorId, currentRole, 'Incident closed in command center');
      }
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Failed to update incident state');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAddNote = async () => {
    if (!selectedIncidentId || !newNote.trim()) return;
    try {
      setIsSubmitting(true);
      await api.addIncidentNote(selectedIncidentId, currentOperatorId, currentRole, newNote.trim());
      setNewNote('');
      const nts = await api.getIncidentNotes(selectedIncidentId);
      setNotes(nts);
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Failed to add note');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'DETECTED':
      case 'VERIFIED':
      case 'CORRELATED':
      case 'ASSESSED':
        return 'bg-[#FF4D4D] text-[#FFFFFF] font-bold';
      case 'ACKNOWLEDGED':
        return 'bg-[#F5A623] text-[#171717] font-bold';
      case 'INVESTIGATING':
        return 'bg-[#171717] text-[#C7FF3D] font-bold';
      case 'CLOSED':
        return 'bg-[#ECE9E0] text-[#5E5E5E] border border-[#D6D2C8]';
      default:
        return 'bg-[#ECE9E0] text-[#171717] border border-[#D6D2C8]';
    }
  };

  return (
    <div className="space-y-4 font-sans">
      <OfflineBanner
        connectivity={connectivity}
        pendingCount={syncSummary?.pending_count}
        onRestore={handleToggleConnectivity}
      />

      {/* Header Toolbar */}
      <div className="bg-[#ECE9E0] border border-[#D6D2C8] rounded-sm p-3.5 shadow-none flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 font-mono">
            <ShieldAlert className="w-4 h-4 text-[#171717]" />
            <div>
              <h2 className="text-xs font-bold text-[#171717] uppercase tracking-wider">
                COMMAND & INCIDENT RESPONSE COCKPIT
              </h2>
              <p className="text-[10px] text-[#5E5E5E]">
                7-STAGE DETERMINISTIC LIFECYCLE • FORWARD PREDICTION • OPERATOR AUDIT TRAIL
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap font-mono text-xs">
          <ConnectionStatus
            connectivity={connectivity}
            summary={syncSummary}
            onToggleOffline={handleToggleConnectivity}
            onOpenSyncDrawer={() => setIsSyncDrawerOpen(true)}
            loading={isTogglingConnectivity}
          />

          <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-0.5 flex items-center">
            {['ALL', 'ACTIVE', 'ACKNOWLEDGED', 'INVESTIGATING', 'CLOSED'].map((st) => (
              <button
                key={st}
                onClick={() => setFilterStatus(st)}
                className={`px-2 py-0.5 rounded-sm transition text-[10px] font-semibold ${
                  filterStatus === st
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
              placeholder="SEARCH INCIDENT..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm pl-6 pr-2 py-0.5 text-[11px] text-[#171717] placeholder-[#8A877E] focus:outline-none focus:border-[#171717] w-36 sm:w-44"
            />
            <Search className="w-3 h-3 text-[#8A877E] absolute left-1.5 top-1.5" />
          </div>
        </div>
      </div>

      {/* Main Split Cockpit */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 items-start font-mono">
        {/* Left: Queue */}
        <div className="xl:col-span-1 space-y-3">
          <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-3 shadow-none space-y-2.5">
            <div className="flex items-center justify-between border-b border-[#ECE9E0] pb-2">
              <span className="text-xs font-bold text-[#171717] uppercase flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-[#171717]" />
                OPERATIONAL QUEUE ({filteredIncidents.length})
              </span>
              <span className="text-[10px] text-[#5E5E5E]">SOC TRIAGE</span>
            </div>

            {filteredIncidents.length === 0 ? (
              <div className="p-8 text-center text-[#5E5E5E] text-xs flex flex-col items-center justify-center gap-1">
                <ShieldAlert className="w-6 h-6 text-[#8A877E]" />
                <span>No incidents matching filter.</span>
              </div>
            ) : (
              <div className="space-y-1.5 max-h-[750px] overflow-y-auto pr-1">
                {filteredIncidents.map((inc) => {
                  const isSelected = selectedIncidentId === inc.incident_id;

                  return (
                    <div
                      key={inc.incident_id}
                      onClick={() => setSelectedIncidentId(inc.incident_id)}
                      className={`p-2.5 rounded-sm border transition cursor-pointer flex flex-col gap-1.5 ${
                        isSelected
                          ? 'bg-[#F4F1E8] border-[#171717] ring-1 ring-[#171717]'
                          : 'bg-[#FFFFFF] border-[#D6D2C8] hover:border-[#171717]/60'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5">
                          <span className="px-1.5 py-0.2 bg-[#171717] text-[#C7FF3D] text-[10px] font-bold rounded-sm">
                            {inc.incident_id}
                          </span>
                          <span className="text-xs font-bold text-[#171717]">
                            {inc.subject_id}
                          </span>
                        </div>
                        <span className={`px-1.5 py-0.2 rounded-sm text-[9px] ${getStatusBadge(inc.status)}`}>
                          {inc.status}
                        </span>
                      </div>

                      <div className="font-bold text-xs text-[#171717] line-clamp-1">
                        {inc.title}
                      </div>

                      <div className="flex items-center justify-between text-[10px] text-[#5E5E5E]">
                        <span>CAMS: {inc.cameras_involved?.join(', ')}</span>
                        <span>{new Date(inc.created_at).toLocaleTimeString()}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right: Active Investigation Console */}
        <div className="xl:col-span-2 space-y-4">
          {lifecycle && narrative ? (
            <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-4 shadow-none space-y-4">
              {/* Top Bar */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#ECE9E0] pb-3">
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="px-2 py-0.5 bg-[#171717] text-[#C7FF3D] rounded-sm text-xs font-bold">
                      {lifecycle.incident_id}
                    </span>
                    <span className="text-xs text-[#5E5E5E]">
                      SUBJECT: <strong className="text-[#171717]">{lifecycle.subject_id}</strong>
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-[#171717] mt-1">
                    {narrative.narrative_title || 'Border Security Incident Cockpit'}
                  </h3>
                </div>

                {/* State Transition Actions */}
                <div className="flex items-center gap-1.5 flex-wrap text-xs">
                  {lifecycle.allowed_transitions?.includes('ACKNOWLEDGED') && (
                    <button
                      onClick={() => handleTransition('ACKNOWLEDGED')}
                      disabled={isSubmitting}
                      className="px-2.5 py-1 bg-[#F5A623] hover:bg-[#d98216] text-[#171717] rounded-sm font-bold transition flex items-center gap-1"
                    >
                      <UserCheck className="w-3 h-3" />
                      <span>ACKNOWLEDGE</span>
                    </button>
                  )}

                  {lifecycle.allowed_transitions?.includes('INVESTIGATING') && (
                    <button
                      onClick={() => handleTransition('INVESTIGATING')}
                      disabled={isSubmitting}
                      className="px-2.5 py-1 bg-[#171717] hover:bg-[#292929] text-[#C7FF3D] rounded-sm font-bold transition flex items-center gap-1"
                    >
                      <Eye className="w-3 h-3" />
                      <span>INVESTIGATE</span>
                    </button>
                  )}

                  {lifecycle.allowed_transitions?.includes('CLOSED') && (
                    <button
                      onClick={() => handleTransition('CLOSED')}
                      disabled={isSubmitting}
                      className="px-2.5 py-1 bg-[#171717] hover:bg-[#292929] text-[#F4F1E8] rounded-sm font-bold transition flex items-center gap-1"
                    >
                      <CheckCircle2 className="w-3 h-3 text-[#C7FF3D]" />
                      <span>CLOSE INCIDENT</span>
                    </button>
                  )}

                  <button
                    onClick={() => onSelectIncidentModal(selectedIncidentId)}
                    className="px-2.5 py-1 bg-[#FFFFFF] hover:bg-[#F4F1E8] text-[#171717] rounded-sm transition border border-[#D6D2C8] flex items-center gap-1"
                  >
                    <Maximize2 className="w-3 h-3" />
                    <span>MODAL</span>
                  </button>
                </div>
              </div>

              {/* 7-Stage Lifecycle Stepper */}
              <div className="space-y-1.5">
                <span className="text-xs font-bold text-[#171717] uppercase">
                  7-STAGE DETERMINISTIC LIFECYCLE
                </span>

                <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-1.5">
                  {lifecycle.stages?.map((st) => (
                    <div
                      key={st.stage_name}
                      className={`p-2 rounded-sm border text-center flex flex-col items-center justify-between gap-1 transition ${
                        st.is_current
                          ? 'bg-[#171717] border-[#171717] text-[#C7FF3D]'
                          : st.is_completed
                          ? 'bg-[#F4F1E8] border-[#D6D2C8] text-[#171717]'
                          : 'bg-[#FFFFFF] border-[#D6D2C8] text-[#8A877E]'
                      }`}
                    >
                      <span className="text-[9px] font-bold block">{st.display_name}</span>
                      {st.is_completed ? (
                        <CheckCircle2 className="w-3 h-3 text-[#1A5319]" />
                      ) : st.is_current ? (
                        <div className="w-1.5 h-1.5 rounded-full bg-[#C7FF3D] animate-ping my-0.5" />
                      ) : (
                        <div className="w-1.5 h-1.5 rounded-full bg-[#D6D2C8] my-0.5" />
                      )}
                      <span className="text-[8px] text-[#5E5E5E] truncate">
                        {st.completed_at ? new Date(st.completed_at).toLocaleTimeString() : 'Pending'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* AI Narrative */}
              <div className="bg-[#F4F1E8] border border-[#D6D2C8] rounded-sm p-3 space-y-2">
                <span className="text-[11px] font-bold text-[#171717] uppercase block">
                  OBJECTIVE AI OPERATIONAL NARRATIVE
                </span>
                <p className="text-xs text-[#171717] leading-relaxed">
                  {narrative.summary}
                </p>
                {narrative.recommendation && (
                  <div className="p-2 rounded-sm bg-[#FFFFFF] border border-[#D6D2C8] text-[11px] text-[#171717]">
                    <strong>RECOMMENDED RESPONSE:</strong> {narrative.recommendation}
                  </div>
                )}
              </div>

              {/* Recommended Forward Tracking Cameras */}
              {recommendedCams && recommendedCams.recommended_cameras?.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-xs font-bold text-[#171717] uppercase flex items-center gap-1">
                    <Compass className="w-3.5 h-3.5 text-[#171717]" />
                    TOPOLOGY-GROUNDED FORWARD PREDICTIONS
                  </span>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {recommendedCams.recommended_cameras.map((rec) => (
                      <div
                        key={rec.camera_id}
                        className="p-2.5 bg-[#F4F1E8] border border-[#D6D2C8] rounded-sm flex flex-col justify-between gap-1.5"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-xs text-[#171717]">
                            {rec.camera_id} ({rec.camera_name})
                          </span>
                          <span className="px-1.5 py-0.2 bg-[#171717] text-[#C7FF3D] rounded-sm text-[9px] font-bold">
                            {(rec.confidence * 100).toFixed(0)}% LIKELY
                          </span>
                        </div>

                        <p className="text-[10px] text-[#5E5E5E]">{rec.reason}</p>

                        <div className="flex items-center justify-between pt-1 border-t border-[#D6D2C8] text-[10px]">
                          <span className="text-[#5E5E5E]">
                            EST. TRANSIT: ~{rec.transition_time_estimate_sec}s
                          </span>
                          <button
                            onClick={() => onFocusCamera(rec.camera_id)}
                            className="px-1.5 py-0.2 bg-[#171717] hover:bg-[#292929] text-[#F4F1E8] rounded-sm text-[9px] font-bold"
                          >
                            FOCUS CAM
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Collaborative Notes & Audit Log */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {/* Notes */}
                <div className="bg-[#F4F1E8] border border-[#D6D2C8] rounded-sm p-3 space-y-2 flex flex-col">
                  <span className="text-xs font-bold text-[#171717] uppercase flex items-center gap-1">
                    <MessageSquare className="w-3.5 h-3.5 text-[#171717]" />
                    OPERATOR NOTES ({notes.length})
                  </span>

                  <div className="flex-1 max-h-40 overflow-y-auto space-y-1.5 pr-1">
                    {notes.length === 0 ? (
                      <p className="text-xs text-[#5E5E5E] p-1">No notes recorded.</p>
                    ) : (
                      notes.map((n) => (
                        <div key={n.note_id} className="p-2 bg-[#FFFFFF] rounded-sm border border-[#D6D2C8] text-xs">
                          <div className="flex items-center justify-between text-[9px] text-[#5E5E5E]">
                            <span className="font-bold text-[#171717]">{n.operator_id} ({n.role})</span>
                            <span>{new Date(n.timestamp).toLocaleTimeString()}</span>
                          </div>
                          <p className="text-[#171717] mt-0.5">{n.note}</p>
                        </div>
                      ))
                    )}
                  </div>

                  <div className="flex items-center gap-1 pt-1.5 border-t border-[#D6D2C8]">
                    <input
                      type="text"
                      placeholder="Add investigation note..."
                      value={newNote}
                      onChange={(e) => setNewNote(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleAddNote()}
                      className="flex-1 bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm px-2 py-0.5 text-xs text-[#171717] focus:outline-none"
                    />
                    <button
                      onClick={handleAddNote}
                      disabled={isSubmitting || !newNote.trim()}
                      className="p-1.5 bg-[#171717] hover:bg-[#292929] text-[#F4F1E8] rounded-sm transition disabled:opacity-50"
                    >
                      <Send className="w-3 h-3 text-[#C7FF3D]" />
                    </button>
                  </div>
                </div>

                {/* Audit Actions */}
                <div className="bg-[#F4F1E8] border border-[#D6D2C8] rounded-sm p-3 space-y-2 flex flex-col">
                  <span className="text-xs font-bold text-[#171717] uppercase flex items-center gap-1">
                    <Lock className="w-3.5 h-3.5 text-[#171717]" />
                    IMMUTABLE AUDIT TRAIL ({actions.length})
                  </span>

                  <div className="flex-1 max-h-48 overflow-y-auto space-y-1.5 pr-1">
                    {actions.length === 0 ? (
                      <p className="text-xs text-[#5E5E5E] p-1">No actions logged.</p>
                    ) : (
                      actions.map((act) => (
                        <div key={act.action_id} className="p-2 bg-[#FFFFFF] rounded-sm border border-[#D6D2C8] text-[10px]">
                          <div className="flex items-center justify-between text-[#5E5E5E]">
                            <span className="font-bold text-[#171717]">{act.action}</span>
                            <span>{new Date(act.timestamp).toLocaleTimeString()}</span>
                          </div>
                          <span className="text-[#5E5E5E] block mt-0.5">
                            BY {act.operator_id} ({act.role})
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-12 text-center text-[#5E5E5E] text-xs">
              Select an incident from the operational queue to inspect.
            </div>
          )}
        </div>
      </div>

      <SyncStatusDrawer
        isOpen={isSyncDrawerOpen}
        onClose={() => setIsSyncDrawerOpen(false)}
        connectivity={connectivity}
        onRefreshParent={fetchConnectivityAndSync}
      />
    </div>
  );
};
