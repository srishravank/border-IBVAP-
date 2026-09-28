import React, { useState, useEffect, useCallback } from 'react';
import {
  Camera,
  SystemHealth,
  CameraEvent,
  CreateCameraPayload,
  GlobalAIStatus,
  Zone,
  SecurityEvent,
  CandidateSummary,
  Subject,
  Incident,
  SectorRisk,
  CommandAlert,
  UserRole,
} from './types';
import { api } from './services/api';
import { Header, DashboardViewType } from './components/Header';
import { AlertBanner } from './components/AlertBanner';
import { OverviewView } from './views/OverviewView';
import { VideoMatrixView } from './views/VideoMatrixView';
import { VirtualZonesView } from './views/VirtualZonesView';
import { CrossCameraView } from './views/CrossCameraView';
import { RiskEngineView } from './views/RiskEngineView';
import { IncidentCommandView } from './views/IncidentCommandView';
import { AuditForensicsView } from './views/AuditForensicsView';
import { LearningView } from './views/LearningView';
import { SimulationLabView } from './views/SimulationLabView';

// Modals
import { IncidentInvestigationModal } from './components/IncidentInvestigationModal';
import { AddCameraModal } from './components/AddCameraModal';
import { ActiveTracksModal } from './components/ActiveTracksModal';
import { EventDetailModal } from './components/EventDetailModal';
import { ZoneDrawerModal } from './components/ZoneDrawerModal';
import { SubjectJourneyModal } from './components/SubjectJourneyModal';
import { IncidentGraphModal } from './components/IncidentGraphModal';
import { TopologyModal } from './components/TopologyModal';
import { RiskAssessmentModal } from './components/RiskAssessmentModal';
import { RiskConfigModal } from './components/RiskConfigModal';

export const App: React.FC = () => {
  // Navigation & View State
  const [currentView, setCurrentView] = useState<DashboardViewType>('OVERVIEW');

  // Core Data State
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [aiStatus, setAiStatus] = useState<GlobalAIStatus | null>(null);
  const [events, setEvents] = useState<CameraEvent[]>([]);
  const [zones, setZones] = useState<Zone[]>([]);
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([]);
  const [candidates, setCandidates] = useState<CandidateSummary[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [sectorRisks, setSectorRisks] = useState<SectorRisk[]>([]);
  const [alerts, setAlerts] = useState<CommandAlert[]>([]);
  const [wsConnected, setWsConnected] = useState<boolean>(false);

  // Operator & Role State (Phase 6)
  const [currentRole, setCurrentRole] = useState<UserRole>('OPERATOR');
  const [currentOperatorId] = useState<string>('OP-9402');
  const [juryMode, setJuryMode] = useState<boolean>(false);

  // Theme State ('light' | 'dark') - default light
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    return (localStorage.getItem('ibvap_theme') as 'light' | 'dark') || 'light';
  });

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
      document.documentElement.classList.remove('light');
      document.body.classList.add('dark');
      document.body.classList.remove('light');
    } else {
      document.documentElement.classList.add('light');
      document.documentElement.classList.remove('dark');
      document.body.classList.add('light');
      document.body.classList.remove('dark');
    }
    localStorage.setItem('ibvap_theme', theme);
  }, [theme]);

  const handleToggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  // Filters & Focus State
  const [selectedSectorId, setSelectedSectorId] = useState<string | null>(null);
  const [focusedCameraId, setFocusedCameraId] = useState<string | null>(null);

  // Modals state
  const [inspectingCameraId, setInspectingCameraId] = useState<string | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false);
  const [selectedSecurityEvent, setSelectedSecurityEvent] = useState<SecurityEvent | null>(null);
  const [zoneDrawerCamera, setZoneDrawerCamera] = useState<Camera | null>(null);
  const [selectedSubjectId, setSelectedSubjectId] = useState<string | null>(null);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [selectedRiskIncidentId, setSelectedRiskIncidentId] = useState<string | null>(null);
  const [investigatingIncidentId, setInvestigatingIncidentId] = useState<string | null>(null);
  const [isTopologyModalOpen, setIsTopologyModalOpen] = useState<boolean>(false);
  const [isRiskConfigOpen, setIsRiskConfigOpen] = useState<boolean>(false);

  // Active right sidebar tab in Overview view: 'INCIDENTS' | 'JOURNEYS' | 'HEALTH'
  const [activeSidebarTab, setActiveSidebarTab] = useState<'INCIDENTS' | 'JOURNEYS' | 'HEALTH'>('JOURNEYS');

  // Fetch all dashboard data
  const fetchData = useCallback(async () => {
    try {
      const [
        camsData,
        healthData,
        aiData,
        zonesData,
        eventsData,
        candidatesData,
        subjsData,
        incsData,
        sectorsData,
        alertsData,
      ] = await Promise.all([
        api.getCameras().catch(() => []),
        api.getHealth().catch(() => null),
        api.getAIStatus().catch(() => null),
        api.getZones().catch(() => []),
        api.getSecurityEvents({ limit: 50 }).catch(() => []),
        api.getVerifyingCandidates().catch(() => []),
        api.getSubjects().catch(() => []),
        api.getIncidents().catch(() => []),
        api.getSectorRisks().catch(() => []),
        api.getAlerts(20).catch(() => []),
      ]);

      setCameras(camsData);
      setHealth(healthData);
      if (aiData) setAiStatus(aiData);
      setZones(zonesData);
      setSecurityEvents(eventsData);
      setCandidates(candidatesData);
      setSubjects(subjsData);
      setIncidents(incsData);
      setSectorRisks(sectorsData);
      setAlerts(alertsData);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    }
  }, []);

  // Initialize and WebSocket listener
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 1500);

    // Setup WebSocket for real-time camera state and health/AI events
    let ws: WebSocket | null = null;
    let reconnectTimeout: any = null;

    const connectWs = () => {
      const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${proto}//${window.location.host}/api/ws/events`;

      try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          setWsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.event_type === 'INITIAL_STATE' && Array.isArray(data.cameras)) {
              setCameras(data.cameras);
            } else if (data.event_type) {
              const newEvt: CameraEvent = data;
              setEvents((prev) => [newEvt, ...prev].slice(0, 100));
              fetchData();
            }
          } catch (e) {
            console.error('WS parse error:', e);
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
          reconnectTimeout = setTimeout(connectWs, 3000);
        };

        ws.onerror = () => {
          setWsConnected(false);
        };
      } catch (e) {
        setWsConnected(false);
        reconnectTimeout = setTimeout(connectWs, 3000);
      }
    };

    connectWs();

    return () => {
      clearInterval(interval);
      if (ws) ws.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, [fetchData]);

  // Handlers
  const handleToggleIngestion = async (id: string, isLive: boolean) => {
    try {
      if (isLive) {
        await api.stopCamera(id);
      } else {
        await api.startCamera(id);
      }
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateCamera = async (payload: CreateCameraPayload) => {
    await api.createCamera(payload);
    fetchData();
  };

  const handleAcknowledgeEvent = async (eventId: string) => {
    try {
      await api.acknowledgeEvent(eventId, `Operator (${currentRole})`);
      fetchData();
    } catch (err) {
      console.error('Failed to acknowledge event:', err);
    }
  };

  // Quick Action Handlers for Incidents
  const handleQuickAcknowledge = async (incidentId: string) => {
    try {
      await api.acknowledgeIncident(
        incidentId,
        currentOperatorId,
        currentRole,
        'Quick acknowledged from command queue'
      );
      fetchData();
    } catch (err: any) {
      alert(err.message || 'Failed to acknowledge incident');
    }
  };

  const handleQuickInvestigate = async (incidentId: string) => {
    try {
      await api.investigateIncident(
        incidentId,
        currentOperatorId,
        currentRole,
        'Quick investigation launched from command queue'
      );
      fetchData();
    } catch (err: any) {
      alert(err.message || 'Failed to start investigation');
    }
  };

  const handleQuickClose = async (incidentId: string) => {
    try {
      await api.closeIncident(
        incidentId,
        currentOperatorId,
        currentRole,
        'Quick closed from command queue'
      );
      fetchData();
    } catch (err: any) {
      alert(err.message || 'Failed to close incident');
    }
  };

  return (
    <div className="min-h-screen bg-forensic-bg text-forensic-text flex flex-col font-sans selection:bg-[#C7FF3D] selection:text-[#171717]">
      {/* Top Telemetry & Navigation Header */}
      <Header
        health={health}
        aiStatus={aiStatus}
        wsConnected={wsConnected}
        totalZones={zones.length}
        confirmedEventsCount={
          securityEvents.filter(
            (e) => e.status !== 'ACKNOWLEDGED' && !e.acknowledged_at
          ).length
        }
        activeSubjectsCount={subjects.length}
        totalIncidentsCount={incidents.filter((i) => i.status !== 'CLOSED').length}
        currentRole={currentRole}
        currentView={currentView}
        juryMode={juryMode}
        theme={theme}
        onToggleJuryMode={() => setJuryMode(!juryMode)}
        onToggleTheme={handleToggleTheme}
        onViewChange={setCurrentView}
        onRoleChange={setCurrentRole}
        onAddCamera={() => setIsAddModalOpen(true)}
        onOpenTopology={() => setIsTopologyModalOpen(true)}
        onOpenRiskConfig={() => setIsRiskConfigOpen(true)}
        onRefresh={fetchData}
      />

      {/* Jury Mode Presentation Streamline Banner */}
      {juryMode && (
        <div className="bg-[#171717] text-[#F4F1E8] border-b-2 border-[#C7FF3D] px-6 py-2.5 flex flex-wrap items-center justify-between gap-4 font-mono text-xs z-40 shadow-sm animate-fadeIn">
          <div className="flex items-center gap-3">
            <span className="flex h-2.5 w-2.5 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#C7FF3D] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#C7FF3D]"></span>
            </span>
            <span className="font-bold tracking-widest text-[#C7FF3D] uppercase">
              JURY VERIFICATION ACTIVE // FULL-SPECTRUM AUDIT
            </span>
            <span className="text-[#888884] text-[10px] hidden md:inline">
              | ISO/IEC 27037 FORENSIC CHAIN EVIDENCE
            </span>
          </div>

          {/* Pipeline flow visualizer */}
          <div className="flex items-center gap-2 overflow-x-auto text-[11px]">
            <span className="bg-[#292929] px-2 py-0.5 border border-[#444] rounded text-neutral-300">
              01 DETECTION
            </span>
            <span className="text-[#C7FF3D]">→</span>
            <span className="bg-[#292929] px-2 py-0.5 border border-[#444] rounded text-neutral-300">
              02 BYTETRACK
            </span>
            <span className="text-[#C7FF3D]">→</span>
            <span className="bg-[#292929] px-2 py-0.5 border border-[#444] rounded text-neutral-300">
              03 RE-ID TRANSIT
            </span>
            <span className="text-[#C7FF3D]">→</span>
            <span className="bg-[#292929] px-2 py-0.5 border border-[#444] rounded text-neutral-300">
              04 RISK ENGINE
            </span>
            <span className="text-[#C7FF3D]">→</span>
            <span className="bg-[#292929] px-2 py-0.5 border border-[#444] rounded text-neutral-300">
              05 SHA-256
            </span>
            <span className="text-[#C7FF3D]">→</span>
            <span className="bg-[#1f301b] border border-[#C7FF3D] text-[#C7FF3D] px-2 py-0.5 rounded font-bold">
              06 CHAIN COMMIT
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setCurrentView('SIMULATION_LAB')}
              className="px-2.5 py-1 bg-[#C7FF3D] text-[#171717] font-bold text-[10px] tracking-wider uppercase hover:bg-[#b5f028] transition-colors rounded"
            >
              RUN TEST RUNNER
            </button>
            <button
              onClick={() => setJuryMode(false)}
              className="text-[#888884] hover:text-[#F4F1E8] text-[10px] uppercase underline underline-offset-2"
            >
              EXIT
            </button>
          </div>
        </div>
      )}

      {/* Real-Time Security Alert Ticker Banner */}
      <AlertBanner
        alerts={alerts}
        onSelectIncident={(incId) => setInvestigatingIncidentId(incId)}
        onAcknowledge={(alertId) => fetchData()}
      />

      {/* Main Monitoring Workspace */}
      <main className="flex-1 p-4 sm:p-6 max-w-[1920px] mx-auto w-full">
        {currentView === 'OVERVIEW' && (
          <OverviewView
            cameras={cameras}
            incidents={incidents}
            sectorRisks={sectorRisks}
            securityEvents={securityEvents}
            candidates={candidates}
            subjects={subjects}
            events={events}
            alerts={alerts}
            selectedSectorId={selectedSectorId}
            focusedCameraId={focusedCameraId}
            currentRole={currentRole}
            currentOperatorId={currentOperatorId}
            activeSidebarTab={activeSidebarTab}
            onSelectSector={setSelectedSectorId}
            onFocusCamera={(camId) => setFocusedCameraId(camId)}
            onToggleIngestion={handleToggleIngestion}
            onInspectTracks={(id) => setInspectingCameraId(id)}
            onConfigureZones={(cam) => setZoneDrawerCamera(cam)}
            onSelectIncident={(incId) => setInvestigatingIncidentId(incId)}
            onQuickAcknowledge={handleQuickAcknowledge}
            onQuickInvestigate={handleQuickInvestigate}
            onQuickClose={handleQuickClose}
            onSelectSubject={(subjId) => {
              setSelectedSubjectId(subjId);
              setActiveSidebarTab('JOURNEYS');
            }}
            onSelectSecurityEvent={(evt) => setSelectedSecurityEvent(evt)}
            onSelectIncidentGraph={(incId) => setSelectedIncidentId(incId)}
            onSetActiveSidebarTab={setActiveSidebarTab}
            onClearHealthEvents={() => setEvents([])}
            onRefresh={fetchData}
          />
        )}

        {currentView === 'VIDEO_MATRIX' && (
          <VideoMatrixView
            cameras={cameras}
            incidents={incidents}
            zones={zones}
            onToggleIngestion={handleToggleIngestion}
            onInspectTracks={(id) => setInspectingCameraId(id)}
            onConfigureZones={(cam) => setZoneDrawerCamera(cam)}
            onSelectIncident={(incId) => setInvestigatingIncidentId(incId)}
            onAddCamera={() => setIsAddModalOpen(true)}
            onRefresh={fetchData}
          />
        )}

        {currentView === 'VIRTUAL_ZONES' && (
          <VirtualZonesView
            cameras={cameras}
            zones={zones}
            securityEvents={securityEvents}
            candidates={candidates}
            onConfigureZones={(cam) => setZoneDrawerCamera(cam)}
            onSelectSecurityEvent={(evt) => setSelectedSecurityEvent(evt)}
            onRefresh={fetchData}
          />
        )}

        {currentView === 'CROSS_CAMERA' && (
          <CrossCameraView
            subjects={subjects}
            incidents={incidents}
            cameras={cameras}
            onOpenTopology={() => setIsTopologyModalOpen(true)}
            onSelectIncident={(incId) => setInvestigatingIncidentId(incId)}
            onSelectIncidentGraph={(incId) => setSelectedIncidentId(incId)}
            onSelectSubjectJourney={(subjId) => setSelectedSubjectId(subjId)}
            onRefresh={fetchData}
          />
        )}

        {currentView === 'RISK_ENGINE' && (
          <RiskEngineView
            incidents={incidents}
            sectorRisks={sectorRisks}
            onOpenRiskConfig={() => setIsRiskConfigOpen(true)}
            onSelectIncident={(incId) => setInvestigatingIncidentId(incId)}
            onRefresh={fetchData}
          />
        )}

        {currentView === 'INCIDENT_COMMAND' && (
          <IncidentCommandView
            incidents={incidents}
            currentRole={currentRole}
            currentOperatorId={currentOperatorId}
            onSelectIncidentModal={(incId) => setInvestigatingIncidentId(incId)}
            onFocusCamera={(camId) => {
              setFocusedCameraId(camId);
              setCurrentView('VIDEO_MATRIX');
            }}
            onRefresh={fetchData}
          />
        )}

        {currentView === 'AUDIT_FORENSICS' && (
          <AuditForensicsView
            currentRole={currentRole}
            currentOperatorId={currentOperatorId}
            onRefresh={fetchData}
          />
        )}

        {currentView === 'FEDERATED_LEARNING' && (
          <LearningView
            currentRole={currentRole}
            currentOperatorId={currentOperatorId}
          />
        )}

        {currentView === 'SIMULATION_LAB' && (
          <SimulationLabView
            onRefresh={fetchData}
            onSelectSubject={(subjId) => {
              setSelectedSubjectId(subjId);
              setCurrentView('CROSS_CAMERA');
            }}
            onSelectIncident={(incId) => {
              setInvestigatingIncidentId(incId);
              setCurrentView('INCIDENT_COMMAND');
            }}
          />
        )}
      </main>

      {/* Phase 6: SOC Incident Investigation Cockpit Modal */}
      {investigatingIncidentId && (
        <IncidentInvestigationModal
          incidentId={investigatingIncidentId}
          currentRole={currentRole}
          currentOperatorId={currentOperatorId}
          onClose={() => setInvestigatingIncidentId(null)}
          onOpenIncidentGraph={(incId) => {
            setSelectedIncidentId(incId);
          }}
          onFocusCamera={(camId) => {
            setFocusedCameraId(camId);
            setCurrentView('VIDEO_MATRIX');
          }}
          onRefreshParent={fetchData}
        />
      )}

      {/* Register Camera Modal */}
      <AddCameraModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onSubmit={handleCreateCamera}
      />

      {/* Active Tracks & Trajectory Modal Inspector */}
      <ActiveTracksModal
        cameraId={inspectingCameraId}
        onClose={() => setInspectingCameraId(null)}
      />

      {/* Virtual Zone Drawer Modal */}
      {zoneDrawerCamera && (
        <ZoneDrawerModal
          cameraId={zoneDrawerCamera.camera_id}
          cameras={cameras}
          onClose={() => setZoneDrawerCamera(null)}
          onZoneUpdated={fetchData}
        />
      )}

      {/* Event Verification Detail Modal */}
      <EventDetailModal
        event={selectedSecurityEvent}
        onClose={() => setSelectedSecurityEvent(null)}
        onAcknowledge={handleAcknowledgeEvent}
      />

      {/* Subject Journey Modal */}
      <SubjectJourneyModal
        subjectId={selectedSubjectId}
        onClose={() => setSelectedSubjectId(null)}
      />

      {/* Incident Graph Modal */}
      <IncidentGraphModal
        incidentId={selectedIncidentId}
        onClose={() => setSelectedIncidentId(null)}
      />

      {/* Camera Topology Configuration Modal */}
      <TopologyModal
        isOpen={isTopologyModalOpen}
        cameras={cameras}
        onClose={() => setIsTopologyModalOpen(false)}
        onUpdated={fetchData}
      />

      {/* Explainable Risk Assessment Modal */}
      {selectedRiskIncidentId && (
        <RiskAssessmentModal
          incidentId={selectedRiskIncidentId}
          onClose={() => setSelectedRiskIncidentId(null)}
          onOpenConfig={() => setIsRiskConfigOpen(true)}
        />
      )}

      {/* Risk Engine Configuration Modal */}
      {isRiskConfigOpen && (
        <RiskConfigModal
          onClose={() => setIsRiskConfigOpen(false)}
          onSaved={fetchData}
        />
      )}
    </div>
  );
};

export default App;
