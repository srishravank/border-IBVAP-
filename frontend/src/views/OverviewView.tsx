import React, { useState } from 'react';
import {
  Camera as CameraType,
  Incident,
  SectorRisk,
  SecurityEvent,
  CandidateSummary,
  Subject,
  CameraEvent,
  UserRole,
} from '../types';
import { SectorRiskMap } from '../components/SectorRiskMap';
import { LiveCameraWall } from '../components/LiveCameraWall';
import { IncidentCommandPanel } from '../components/IncidentCommandPanel';
import { SimulationControls } from '../components/SimulationControls';
import { SecurityEventsPanel } from '../components/SecurityEventsPanel';
import { CameraHealthEvents } from '../components/CameraHealthEvents';
import {
  Compass,
  ShieldAlert,
  Activity,
  ArrowRight,
  FileText,
  Share2,
  Lock,
  CheckCircle2,
  Cpu,
  Layers
} from 'lucide-react';

interface OverviewViewProps {
  cameras: CameraType[];
  incidents: Incident[];
  sectorRisks: SectorRisk[];
  securityEvents: SecurityEvent[];
  candidates: CandidateSummary[];
  subjects: Subject[];
  events: CameraEvent[];
  alerts: any[];
  selectedSectorId: string | null;
  focusedCameraId: string | null;
  currentRole: UserRole;
  currentOperatorId: string;
  activeSidebarTab: 'JOURNEYS' | 'INCIDENTS' | 'HEALTH';
  onSelectSector: (sectorId: string | null) => void;
  onFocusCamera: (cameraId: string | null) => void;
  onToggleIngestion: (id: string, isLive: boolean) => void;
  onInspectTracks: (id: string) => void;
  onConfigureZones: (cam: CameraType) => void;
  onSelectIncident: (incidentId: string) => void;
  onQuickAcknowledge: (incidentId: string) => void;
  onQuickInvestigate: (incidentId: string) => void;
  onQuickClose: (incidentId: string) => void;
  onSelectSubject: (subjectId: string) => void;
  onSelectSecurityEvent: (event: SecurityEvent) => void;
  onSelectIncidentGraph: (incidentId: string) => void;
  onSetActiveSidebarTab: (tab: 'JOURNEYS' | 'INCIDENTS' | 'HEALTH') => void;
  onClearHealthEvents: () => void;
  onRefresh: () => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  cameras,
  incidents,
  sectorRisks,
  securityEvents,
  candidates,
  subjects,
  events,
  selectedSectorId,
  focusedCameraId,
  currentRole,
  activeSidebarTab,
  onSelectSector,
  onFocusCamera,
  onToggleIngestion,
  onInspectTracks,
  onConfigureZones,
  onSelectIncident,
  onQuickAcknowledge,
  onQuickInvestigate,
  onQuickClose,
  onSelectSubject,
  onSelectSecurityEvent,
  onSelectIncidentGraph,
  onSetActiveSidebarTab,
  onClearHealthEvents,
  onRefresh,
}) => {
  const [selectedBlockIdx, setSelectedBlockIdx] = useState<number>(3);

  const blockchainBlocks = [
    {
      num: 'BLOCK 0839',
      hash: '72C4...91A8',
      prev: '5E10...3B92',
      events: 4,
      ts: '20:38:14',
      status: 'VERIFIED',
    },
    {
      num: 'BLOCK 0840',
      hash: '8A91...F2D0',
      prev: '72C4...91A8',
      events: 6,
      ts: '20:39:30',
      status: 'VERIFIED',
    },
    {
      num: 'BLOCK 0841',
      hash: '4B31...88C2',
      prev: '8A91...F2D0',
      events: 3,
      ts: '20:41:05',
      status: 'VERIFIED',
    },
    {
      num: 'BLOCK 0842',
      hash: '91A7...F31C',
      prev: '4B31...88C2',
      events: 5,
      ts: '20:42:17',
      status: 'VERIFIED',
    },
  ];

  return (
    <div className="space-y-4 font-sans">
      {/* Simulation Controls */}
      <SimulationControls
        cameras={cameras}
        onRefresh={onRefresh}
        onSelectSubject={(subjId) => {
          onSelectSubject(subjId);
          onSetActiveSidebarTab('JOURNEYS');
        }}
      />

      {/* Forensic Blockchain Chain Integrity Strip */}
      <div className="bg-[#ECE9E0] border border-[#D6D2C8] rounded-sm p-3 font-mono">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#D6D2C8] pb-2 mb-2.5">
          <div className="flex items-center gap-2">
            <Lock className="w-3.5 h-3.5 text-[#171717]" />
            <span className="font-bold text-xs text-[#171717]">
              IMMUTABLE EVIDENCE LEDGER // CHAIN INTEGRITY PIPELINE
            </span>
          </div>
          <span className="text-[10px] text-[#5E5E5E]">
            RFC 8785 CANONICAL MERKLE TREE • SHA-256 HASH ANCHORED
          </span>
        </div>

        {/* Chain Flow Sequence */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
          {blockchainBlocks.map((blk, idx) => {
            const isLatest = idx === blockchainBlocks.length - 1;
            const isSelected = selectedBlockIdx === idx;

            return (
              <div
                key={blk.num}
                onClick={() => setSelectedBlockIdx(idx)}
                className={`p-2.5 rounded-sm border cursor-pointer transition flex flex-col justify-between gap-1.5 ${
                  isSelected
                    ? 'bg-[#FFFFFF] border-[#171717] ring-1 ring-[#171717]'
                    : 'bg-[#FFFFFF] border-[#D6D2C8] hover:border-[#171717]/60'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-[#171717]">
                    ● {blk.num}
                  </span>
                  <span className="px-1.5 py-0.2 bg-[#171717] text-[#C7FF3D] font-bold text-[8px] rounded-sm">
                    {blk.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-1 text-[9px] text-[#5E5E5E] bg-[#F4F1E8] p-1.5 rounded-sm border border-[#D6D2C8]">
                  <div>
                    <span className="block text-[#8A877E] text-[8px]">HASH</span>
                    <span className="font-bold text-[#171717]">{blk.hash}</span>
                  </div>
                  <div>
                    <span className="block text-[#8A877E] text-[8px]">PREVIOUS</span>
                    <span className="font-bold text-[#171717]">{blk.prev}</span>
                  </div>
                  <div>
                    <span className="block text-[#8A877E] text-[8px]">EVENTS</span>
                    <span className="font-bold text-[#171717]">{blk.events} COMMITTED</span>
                  </div>
                  <div>
                    <span className="block text-[#8A877E] text-[8px]">TIME</span>
                    <span className="font-bold text-[#171717]">{blk.ts}</span>
                  </div>
                </div>

                {isLatest && (
                  <div className="flex items-center gap-1 text-[9px] text-[#1A5319] font-bold">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#1A5319] animate-pulse" />
                    <span>LATEST SYNCED BLOCK // READY</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Tactical Sector Risk Map */}
      <SectorRiskMap
        sectors={sectorRisks}
        selectedSectorId={selectedSectorId}
        onSelectSector={onSelectSector}
        onFocusCamera={onFocusCamera}
      />

      {/* CCTV Forensic Windows Grid + Sidecar Panel */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-4 items-start">
        {/* Main 3 Columns: Forensic Camera Windows + Incident Queue */}
        <div className="xl:col-span-3 space-y-4">
          <LiveCameraWall
            cameras={cameras}
            incidents={incidents}
            focusedCameraId={focusedCameraId}
            onToggleIngestion={onToggleIngestion}
            onFocusCamera={onFocusCamera}
            onInspectTracks={onInspectTracks}
            onConfigureZones={onConfigureZones}
            onSelectIncident={onSelectIncident}
          />

          <IncidentCommandPanel
            incidents={incidents}
            selectedSectorId={selectedSectorId}
            currentRole={currentRole}
            onOpenInvestigation={onSelectIncident}
            onQuickAcknowledge={onQuickAcknowledge}
            onQuickInvestigate={onQuickInvestigate}
            onQuickClose={onQuickClose}
          />
        </div>

        {/* Right Sidecar Panel */}
        <div className="xl:col-span-1 sticky top-24 space-y-2.5">
          {/* Sidecar Tab Switcher */}
          <div className="bg-[#ECE9E0] border border-[#D6D2C8] rounded-sm p-1 flex items-center gap-1 font-mono text-xs">
            <button
              onClick={() => onSetActiveSidebarTab('JOURNEYS')}
              className={`flex-1 py-1.5 rounded-sm font-semibold transition flex items-center justify-center gap-1 text-[11px] ${
                activeSidebarTab === 'JOURNEYS'
                  ? 'bg-[#171717] text-[#C7FF3D]'
                  : 'text-[#5E5E5E] hover:text-[#171717]'
              }`}
            >
              <Compass className="w-3 h-3" />
              <span>JOURNEYS ({subjects.length})</span>
            </button>

            <button
              onClick={() => onSetActiveSidebarTab('INCIDENTS')}
              className={`flex-1 py-1.5 rounded-sm font-semibold transition flex items-center justify-center gap-1 text-[11px] ${
                activeSidebarTab === 'INCIDENTS'
                  ? 'bg-[#171717] text-[#C7FF3D]'
                  : 'text-[#5E5E5E] hover:text-[#171717]'
              }`}
            >
              <ShieldAlert className="w-3 h-3" />
              <span>EVENTS ({securityEvents.length})</span>
            </button>

            <button
              onClick={() => onSetActiveSidebarTab('HEALTH')}
              className={`flex-1 py-1.5 rounded-sm font-semibold transition flex items-center justify-center gap-1 text-[11px] ${
                activeSidebarTab === 'HEALTH'
                  ? 'bg-[#171717] text-[#C7FF3D]'
                  : 'text-[#5E5E5E] hover:text-[#171717]'
              }`}
            >
              <Activity className="w-3 h-3" />
              <span>LOGS</span>
            </button>
          </div>

          {/* Tab Body */}
          {activeSidebarTab === 'JOURNEYS' ? (
            <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm overflow-hidden flex flex-col h-full max-h-[620px]">
              <div className="p-2.5 bg-[#ECE9E0] border-b border-[#D6D2C8] flex items-center justify-between font-mono">
                <span className="text-xs font-bold text-[#171717] uppercase flex items-center gap-1.5">
                  <Compass className="w-3.5 h-3.5 text-[#171717]" />
                  CROSS-CAMERA INTEL ({subjects.length})
                </span>
                <span className="text-[10px] text-[#5E5E5E]">
                  MULTI-HOP RE-ID
                </span>
              </div>

              <div className="flex-1 overflow-y-auto divide-y divide-[#ECE9E0] p-2 space-y-2">
                {subjects.length === 0 ? (
                  <div className="p-8 text-center text-[#5E5E5E] flex flex-col items-center justify-center font-mono">
                    <Compass className="w-6 h-6 text-[#8A877E] mb-1.5" />
                    <p className="text-xs font-bold text-[#171717]">
                      NO CROSS-CAMERA SUBJECTS
                    </p>
                    <p className="text-[10px] text-[#8A877E] mt-1 max-w-xs text-center">
                      Trigger Scenario 04 or 05 in Simulation Controls to generate multi-camera trajectories.
                    </p>
                  </div>
                ) : (
                  subjects.map((subj) => {
                    const cams = Array.from(
                      new Set(subj.track_links.map((l) => l.camera_id))
                    );
                    const inc = incidents.find(
                      (i) => i.subject_id === subj.subject_id
                    );
                    return (
                      <div
                        key={subj.subject_id}
                        className="bg-[#F4F1E8] border border-[#D6D2C8] hover:border-[#171717] rounded-sm p-2.5 flex flex-col gap-1.5 transition font-mono text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5">
                            <span className="px-1.5 py-0.2 bg-[#171717] text-[#C7FF3D] font-bold rounded-sm text-[10px]">
                              {subj.subject_id}
                            </span>
                            <span className="text-[11px] font-bold text-[#171717] uppercase">
                              {subj.object_type}
                            </span>
                          </div>

                          <span className="text-[9px] text-[#5E5E5E]">
                            {new Date(subj.last_seen).toLocaleTimeString()}
                          </span>
                        </div>

                        {/* Visited Cameras */}
                        <div className="flex items-center gap-1 text-[10px] text-[#171717]">
                          <span className="text-[#8A877E] text-[9px]">ROUTE:</span>
                          {cams.map((c, idx) => (
                            <React.Fragment key={c}>
                              <span className="px-1.5 py-0.2 bg-[#FFFFFF] text-[#171717] rounded-sm border border-[#D6D2C8] text-[9px] font-bold">
                                {c}
                              </span>
                              {idx < cams.length - 1 && (
                                <ArrowRight className="w-2.5 h-2.5 text-[#8A877E]" />
                              )}
                            </React.Fragment>
                          ))}
                        </div>

                        {/* Actions */}
                        <div className="pt-1.5 border-t border-[#D6D2C8] flex items-center justify-between gap-1 flex-wrap text-[10px]">
                          <button
                            onClick={() => onSelectSubject(subj.subject_id)}
                            className="px-2 py-0.5 bg-[#FFFFFF] hover:bg-[#171717] hover:text-[#C7FF3D] text-[#171717] border border-[#D6D2C8] rounded-sm font-semibold flex items-center gap-1 transition"
                            title="View Cross-Camera Journey"
                          >
                            <Compass className="w-3 h-3" />
                            <span>JOURNEY</span>
                          </button>

                          {inc && (
                            <div className="flex items-center gap-1">
                              <button
                                onClick={() => onSelectIncident(inc.incident_id)}
                                className="px-2 py-0.5 bg-[#FF4D4D] text-[#FFFFFF] rounded-sm font-bold flex items-center gap-1"
                                title="Open Cockpit"
                              >
                                <FileText className="w-3 h-3" />
                                <span>COCKPIT</span>
                              </button>

                              <button
                                onClick={() =>
                                  onSelectIncidentGraph(inc.incident_id)
                                }
                                className="px-2 py-0.5 bg-[#FFFFFF] hover:bg-[#171717] hover:text-[#C7FF3D] text-[#171717] border border-[#D6D2C8] rounded-sm font-bold flex items-center gap-1"
                                title="Inspect Graph"
                              >
                                <Share2 className="w-3 h-3" />
                                <span>GRAPH</span>
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          ) : activeSidebarTab === 'INCIDENTS' ? (
            <SecurityEventsPanel
              events={securityEvents}
              candidates={candidates}
              onSelectEvent={onSelectSecurityEvent}
              onRefresh={onRefresh}
            />
          ) : (
            <CameraHealthEvents
              events={events}
              selectedCameraId={focusedCameraId}
              onClose={() => onFocusCamera(null)}
              onClearEvents={onClearHealthEvents}
            />
          )}
        </div>
      </div>
    </div>
  );
};
