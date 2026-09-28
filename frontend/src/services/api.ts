import {
  Camera,
  SystemHealth,
  CreateCameraPayload,
  CameraEvent,
  GlobalAIStatus,
  TrackedObject,
  AIPerformanceStats,
  AIObservation,
  Zone,
  CreateZonePayload,
  SecurityEvent,
  VerificationDetail,
  CandidateSummary,
  CameraTopologyRelation,
  Subject,
  SubjectJourney,
  Incident,
  IncidentTimelineEntry,
  IncidentGraphData,
  MatchCandidate,
  RiskAssessment,
  RiskFactor,
  RiskHistoryEntry,
  RiskConfig,
  RiskSummary,
  IncidentIntelligence,
  DashboardSummary,
  SectorRisk,
  RecommendedCamera,
  RecommendedCameraResponse,
  OperatorAction,
  IncidentNote,
  IncidentLifecycle,
  IncidentNarrative,
  CommandAlert,
  EvidencePackage,
  EvidenceManifest,
  LedgerAnchor,
  EvidenceVerificationResult,
  TamperDemoResult,
  EvidenceAuditLogEntry,
  LedgerBlock,
  ConnectionState,
  ConnectivityStatus,
  SyncQueueItem,
  SyncQueueSummary,
  SyncStatusResponse,
  SyncRetryResult,
  ModelVersion,
  ModelValidationResult,
  TrainingSample,
  TrainingRun,
  LocalTrainingStatus,
  ModelUpdate,
  FederatedRound,
  ModelAuditLog,
  PrivacyStatus
} from '../types';

const API_BASE = '/api';

export const api = {
  async getHealth(): Promise<SystemHealth> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Failed to fetch system health');
    return res.json();
  },

  async getAIStatus(): Promise<GlobalAIStatus> {
    const res = await fetch(`${API_BASE}/ai/status`);
    if (!res.ok) throw new Error('Failed to fetch AI status');
    return res.json();
  },

  async getCameras(): Promise<Camera[]> {
    const res = await fetch(`${API_BASE}/cameras`);
    if (!res.ok) throw new Error('Failed to fetch cameras');
    return res.json();
  },

  async getCamera(id: string): Promise<Camera> {
    const res = await fetch(`${API_BASE}/cameras/${id}`);
    if (!res.ok) throw new Error(`Failed to fetch camera ${id}`);
    return res.json();
  },

  async createCamera(payload: CreateCameraPayload): Promise<Camera> {
    const res = await fetch(`${API_BASE}/cameras`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to create camera');
    }
    return res.json();
  },

  async updateCamera(id: string, payload: Partial<CreateCameraPayload>): Promise<Camera> {
    const res = await fetch(`${API_BASE}/cameras/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Failed to update camera ${id}`);
    return res.json();
  },

  async deleteCamera(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/cameras/${id}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(`Failed to delete camera ${id}`);
  },

  async startCamera(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/cameras/${id}/start`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`Failed to start camera ${id}`);
  },

  async stopCamera(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/cameras/${id}/stop`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`Failed to stop camera ${id}`);
  },

  async getCameraStatus(id: string): Promise<{ camera_id: string; status: string; is_alive: boolean; fps: number }> {
    const res = await fetch(`${API_BASE}/cameras/${id}/status`);
    if (!res.ok) throw new Error(`Failed to fetch status for ${id}`);
    return res.json();
  },

  async getCameraEvents(id: string, limit: number = 30): Promise<CameraEvent[]> {
    const res = await fetch(`${API_BASE}/cameras/${id}/events?limit=${limit}`);
    if (!res.ok) throw new Error(`Failed to fetch events for ${id}`);
    return res.json();
  },

  async getCameraTracks(id: string): Promise<TrackedObject[]> {
    const res = await fetch(`${API_BASE}/cameras/${id}/tracks`);
    if (!res.ok) throw new Error(`Failed to fetch tracks for ${id}`);
    return res.json();
  },

  async getCameraDetections(id: string): Promise<any[]> {
    const res = await fetch(`${API_BASE}/cameras/${id}/detections`);
    if (!res.ok) throw new Error(`Failed to fetch detections for ${id}`);
    return res.json();
  },

  async getCameraPerformance(id: string): Promise<AIPerformanceStats> {
    const res = await fetch(`${API_BASE}/cameras/${id}/performance`);
    if (!res.ok) throw new Error(`Failed to fetch AI performance for ${id}`);
    return res.json();
  },

  async getCameraObservations(id: string, limit: number = 20): Promise<AIObservation[]> {
    const res = await fetch(`${API_BASE}/cameras/${id}/observations?limit=${limit}`);
    if (!res.ok) throw new Error(`Failed to fetch observations for ${id}`);
    return res.json();
  },

  // --- Phase 3: Virtual Fence Zones ---
  async getZones(): Promise<Zone[]> {
    const res = await fetch(`${API_BASE}/zones`);
    if (!res.ok) throw new Error('Failed to fetch virtual zones');
    return res.json();
  },

  async getCameraZones(cameraId: string, enabledOnly: boolean = false): Promise<Zone[]> {
    const res = await fetch(`${API_BASE}/cameras/${cameraId}/zones?enabled_only=${enabledOnly}`);
    if (!res.ok) throw new Error(`Failed to fetch zones for camera ${cameraId}`);
    return res.json();
  },

  async createZone(cameraId: string, payload: CreateZonePayload): Promise<Zone> {
    const res = await fetch(`${API_BASE}/cameras/${cameraId}/zones`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to create virtual zone');
    }
    return res.json();
  },

  async updateZone(zoneId: string, payload: Partial<CreateZonePayload>): Promise<Zone> {
    const res = await fetch(`${API_BASE}/zones/${zoneId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Failed to update zone ${zoneId}`);
    return res.json();
  },

  async deleteZone(zoneId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/zones/${zoneId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(`Failed to delete zone ${zoneId}`);
  },

  // --- Phase 3: Security Events & Verification ---
  async getSecurityEvents(filters?: {
    camera_id?: string;
    zone_id?: string;
    event_type?: string;
    status?: string;
    limit?: number;
  }): Promise<SecurityEvent[]> {
    const params = new URLSearchParams();
    if (filters?.camera_id) params.append('camera_id', filters.camera_id);
    if (filters?.zone_id) params.append('zone_id', filters.zone_id);
    if (filters?.event_type) params.append('event_type', filters.event_type);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.limit) params.append('limit', String(filters.limit));

    const res = await fetch(`${API_BASE}/events?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch security events');
    return res.json();
  },

  async getVerifyingCandidates(cameraId?: string): Promise<CandidateSummary[]> {
    const url = cameraId ? `${API_BASE}/events/candidates?camera_id=${cameraId}` : `${API_BASE}/events/candidates`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch verifying candidates');
    return res.json();
  },

  async getSecurityEvent(id: string): Promise<SecurityEvent> {
    const res = await fetch(`${API_BASE}/events/${id}`);
    if (!res.ok) throw new Error(`Failed to fetch event ${id}`);
    return res.json();
  },

  async getEventVerification(id: string): Promise<VerificationDetail> {
    const res = await fetch(`${API_BASE}/events/${id}/verification`);
    if (!res.ok) throw new Error(`Failed to fetch verification for ${id}`);
    return res.json();
  },

  async acknowledgeEvent(id: string, notes?: string): Promise<SecurityEvent> {
    const res = await fetch(`${API_BASE}/events/${id}/acknowledge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ operator_notes: notes }),
    });
    if (!res.ok) throw new Error(`Failed to acknowledge event ${id}`);
    return res.json();
  },

  // --- Phase 4: Camera Topology ---
  async getTopology(): Promise<CameraTopologyRelation[]> {
    const res = await fetch(`${API_BASE}/cameras/topology`);
    if (!res.ok) throw new Error('Failed to fetch camera topology');
    return res.json();
  },

  async createTopology(payload: Partial<CameraTopologyRelation>): Promise<CameraTopologyRelation> {
    const res = await fetch(`${API_BASE}/cameras/topology`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to create camera topology route');
    return res.json();
  },

  async updateTopology(relationId: string, payload: Partial<CameraTopologyRelation>): Promise<CameraTopologyRelation> {
    const res = await fetch(`${API_BASE}/cameras/topology/${relationId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Failed to update topology route ${relationId}`);
    return res.json();
  },

  async deleteTopology(relationId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/cameras/topology/${relationId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(`Failed to delete topology route ${relationId}`);
  },

  // --- Phase 4: Global Subjects & Journeys ---
  async getSubjects(): Promise<Subject[]> {
    const res = await fetch(`${API_BASE}/subjects`);
    if (!res.ok) throw new Error('Failed to fetch global subjects');
    return res.json();
  },

  async getSubject(id: string): Promise<Subject> {
    const res = await fetch(`${API_BASE}/subjects/${id}`);
    if (!res.ok) throw new Error(`Failed to fetch subject ${id}`);
    return res.json();
  },

  async getSubjectJourney(id: string): Promise<SubjectJourney> {
    const res = await fetch(`${API_BASE}/subjects/${id}/journey`);
    if (!res.ok) throw new Error(`Failed to fetch journey for ${id}`);
    return res.json();
  },

  // --- Phase 4: Incidents & Incident Graph ---
  async getIncidents(): Promise<Incident[]> {
    const res = await fetch(`${API_BASE}/incidents`);
    if (!res.ok) throw new Error('Failed to fetch incidents');
    return res.json();
  },

  async getIncidentTimeline(id: string): Promise<IncidentTimelineEntry[]> {
    const res = await fetch(`${API_BASE}/incidents/${id}/timeline`);
    if (!res.ok) throw new Error(`Failed to fetch timeline for incident ${id}`);
    return res.json();
  },

  async getIncidentGraph(id: string): Promise<IncidentGraphData> {
    const res = await fetch(`${API_BASE}/incidents/${id}/graph`);
    if (!res.ok) throw new Error(`Failed to fetch graph for incident ${id}`);
    return res.json();
  },

  async getMatchCandidates(): Promise<MatchCandidate[]> {
    const res = await fetch(`${API_BASE}/incidents/candidates`);
    if (!res.ok) throw new Error('Failed to fetch matching candidates');
    return res.json();
  },

  // --- Phase 4: Deterministic Demo Triggers ---
  async runDemoJourney(): Promise<any> {
    const res = await fetch(`${API_BASE}/demo/cross-camera/journey`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to trigger demo journey');
    return res.json();
  },

  async runDemoFalseMatch(): Promise<any> {
    const res = await fetch(`${API_BASE}/demo/cross-camera/false-match`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to trigger false match demo');
    return res.json();
  },

  async resetDemoState(): Promise<any> {
    const res = await fetch(`${API_BASE}/demo/cross-camera/reset`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to reset demo state');
    return res.json();
  },

  // --- Phase 5: Intelligence & Explainable Risk Engine ---
  async getIncidentRisk(incidentId: string, recalculate: boolean = false): Promise<RiskAssessment> {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}/risk?recalculate=${recalculate}`);
    if (!res.ok) throw new Error(`Failed to fetch risk assessment for incident ${incidentId}`);
    return res.json();
  },

  async getIncidentRiskHistory(incidentId: string): Promise<RiskHistoryEntry[]> {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}/risk/history`);
    if (!res.ok) throw new Error(`Failed to fetch risk history for incident ${incidentId}`);
    return res.json();
  },

  async getIncidentRiskFactors(incidentId: string): Promise<RiskFactor[]> {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}/risk/factors`);
    if (!res.ok) throw new Error(`Failed to fetch risk factors for incident ${incidentId}`);
    return res.json();
  },

  async getRiskConfig(): Promise<RiskConfig> {
    const res = await fetch(`${API_BASE}/risk/config`);
    if (!res.ok) throw new Error('Failed to fetch risk configuration');
    return res.json();
  },

  async updateRiskConfig(payload: Partial<RiskConfig>): Promise<RiskConfig> {
    const res = await fetch(`${API_BASE}/risk/config`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Failed to update risk configuration');
    return res.json();
  },

  async getRiskSummary(): Promise<RiskSummary> {
    const res = await fetch(`${API_BASE}/risk/summary`);
    if (!res.ok) throw new Error('Failed to fetch risk summary');
    return res.json();
  },

  async getIncidentIntelligence(incidentId: string): Promise<IncidentIntelligence> {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}/intelligence`);
    if (!res.ok) throw new Error(`Failed to fetch intelligence object for incident ${incidentId}`);
    return res.json();
  },

  // --- Phase 6: Command & Response Interface APIs ---
  async getDashboardSummary(): Promise<DashboardSummary> {
    const res = await fetch(`${API_BASE}/command/summary`);
    if (!res.ok) throw new Error('Failed to fetch command dashboard summary');
    return res.json();
  },

  async getSectorRisks(): Promise<SectorRisk[]> {
    const res = await fetch(`${API_BASE}/command/sectors`);
    if (!res.ok) throw new Error('Failed to fetch sector risks');
    return res.json();
  },

  async getSectorDetails(sectorId: string): Promise<SectorRisk> {
    const res = await fetch(`${API_BASE}/command/sectors/${sectorId}`);
    if (!res.ok) throw new Error(`Failed to fetch sector details for ${sectorId}`);
    return res.json();
  },

  async getAlerts(limit: number = 50): Promise<CommandAlert[]> {
    const res = await fetch(`${API_BASE}/command/alerts?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch command alerts');
    return res.json();
  },

  async getRecommendedCameras(incidentId: string): Promise<RecommendedCameraResponse> {
    const res = await fetch(`${API_BASE}/command/incidents/${incidentId}/recommended-cameras`);
    if (!res.ok) throw new Error(`Failed to fetch recommended cameras for ${incidentId}`);
    return res.json();
  },

  async getIncidentNarrative(incidentId: string): Promise<IncidentNarrative> {
    const res = await fetch(`${API_BASE}/command/incidents/${incidentId}/narrative`);
    if (!res.ok) throw new Error(`Failed to fetch narrative for ${incidentId}`);
    return res.json();
  },

  async getIncidentLifecycle(incidentId: string): Promise<IncidentLifecycle> {
    const res = await fetch(`${API_BASE}/command/incidents/${incidentId}/lifecycle`);
    if (!res.ok) throw new Error(`Failed to fetch lifecycle for ${incidentId}`);
    return res.json();
  },

  async acknowledgeIncident(incidentId: string, operatorId: string, role: string, notes?: string): Promise<IncidentLifecycle> {
    const res = await fetch(`${API_BASE}/command/incidents/${incidentId}/acknowledge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ operator_id: operatorId, role, notes })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to acknowledge incident ${incidentId}`);
    }
    return res.json();
  },

  async investigateIncident(incidentId: string, operatorId: string, role: string, notes?: string): Promise<IncidentLifecycle> {
    const res = await fetch(`${API_BASE}/command/incidents/${incidentId}/investigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ operator_id: operatorId, role, notes })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to start investigation on incident ${incidentId}`);
    }
    return res.json();
  },

  async closeIncident(incidentId: string, operatorId: string, role: string, notes?: string): Promise<IncidentLifecycle> {
    const res = await fetch(`${API_BASE}/command/incidents/${incidentId}/close`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ operator_id: operatorId, role, notes })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to close incident ${incidentId}`);
    }
    return res.json();
  },

  async getIncidentNotes(incidentId: string): Promise<IncidentNote[]> {
    const res = await fetch(`${API_BASE}/command/incidents/${incidentId}/notes`);
    if (!res.ok) throw new Error(`Failed to fetch notes for ${incidentId}`);
    return res.json();
  },

  async addIncidentNote(incidentId: string, operatorId: string, role: string, note: string): Promise<IncidentNote> {
    const res = await fetch(`${API_BASE}/command/incidents/${incidentId}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ operator_id: operatorId, role, note })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to add note to ${incidentId}`);
    }
    return res.json();
  },

  async getOperatorActions(incidentId?: string, limit: number = 100): Promise<OperatorAction[]> {
    const params = new URLSearchParams();
    if (incidentId) params.append('incident_id', incidentId);
    params.append('limit', String(limit));
    const res = await fetch(`${API_BASE}/command/actions?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch operator action audit trail');
    return res.json();
  },

  async logOperatorAction(payload: {
    incident_id: string;
    operator_id: string;
    role: string;
    action: string;
    notes?: string;
    metadata?: Record<string, any>;
  }): Promise<OperatorAction> {
    const res = await fetch(`${API_BASE}/command/actions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Failed to log operator action');
    return res.json();
  },

  async runScenario(num: number): Promise<any> {
    const res = await fetch(`${API_BASE}/demo/scenario/${num}`, { method: 'POST' });
    if (!res.ok) throw new Error(`Failed to trigger scenario ${num}`);
    return res.json();
  },

  // --- Phase 7: Evidence Trust & Blockchain Anchoring ---

  async getIncidentEvidencePackages(incidentId: string): Promise<EvidencePackage[]> {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}/evidence`);
    if (!res.ok) throw new Error(`Failed to fetch evidence packages for ${incidentId}`);
    return res.json();
  },

  async generateEvidencePackage(
    incidentId: string,
    payload: { operator_id?: string; role?: string; version?: string; notes?: string } = {}
  ): Promise<EvidencePackage> {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}/evidence`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        operator_id: payload.operator_id || 'OP-9402',
        role: payload.role || 'OPERATOR',
        version: payload.version || '1.0',
        notes: payload.notes || ''
      })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to generate evidence package for ${incidentId}`);
    }
    return res.json();
  },

  async getEvidencePackage(evidenceId: string): Promise<EvidencePackage> {
    const res = await fetch(`${API_BASE}/evidence/${evidenceId}`);
    if (!res.ok) throw new Error(`Failed to fetch evidence package ${evidenceId}`);
    return res.json();
  },

  async getEvidenceManifest(evidenceId: string): Promise<EvidenceManifest> {
    const res = await fetch(`${API_BASE}/evidence/${evidenceId}/manifest`);
    if (!res.ok) throw new Error(`Failed to fetch manifest for ${evidenceId}`);
    return res.json();
  },

  async getEvidenceAnchor(evidenceId: string): Promise<LedgerAnchor> {
    const res = await fetch(`${API_BASE}/evidence/${evidenceId}/anchor`);
    if (!res.ok) throw new Error(`Failed to fetch anchor for ${evidenceId}`);
    return res.json();
  },

  async verifyEvidenceIntegrity(
    evidenceId: string,
    payload: { operator_id?: string; role?: string } = {}
  ): Promise<EvidenceVerificationResult> {
    const res = await fetch(`${API_BASE}/evidence/${evidenceId}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        operator_id: payload.operator_id || 'OP-9402',
        role: payload.role || 'OPERATOR'
      })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to verify evidence ${evidenceId}`);
    }
    return res.json();
  },

  async tamperEvidenceDemo(
    evidenceId: string,
    payload: { field?: string; tampered_value?: any } = {}
  ): Promise<TamperDemoResult> {
    const res = await fetch(`${API_BASE}/evidence/${evidenceId}/tamper-demo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to execute tamper demonstration`);
    }
    return res.json();
  },

  async restoreEvidenceDemo(evidenceId: string): Promise<{ status: string; message: string; evidence_id: string }> {
    const res = await fetch(`${API_BASE}/evidence/${evidenceId}/restore-demo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to restore evidence`);
    }
    return res.json();
  },

  async getEvidenceAuditTrail(evidenceId: string): Promise<EvidenceAuditLogEntry[]> {
    const res = await fetch(`${API_BASE}/evidence/${evidenceId}/audit-trail`);
    if (!res.ok) throw new Error(`Failed to fetch evidence audit trail`);
    return res.json();
  },

  async getLedgerBlocks(): Promise<LedgerBlock[]> {
    const res = await fetch(`${API_BASE}/ledger/blocks`);
    if (!res.ok) throw new Error('Failed to fetch blockchain ledger blocks');
    return res.json();
  },

  // --- Phase 8: Offline-First Operation & Resilient Synchronization ---

  async getConnectivityStatus(): Promise<ConnectivityStatus> {
    const res = await fetch(`${API_BASE}/system/connectivity`);
    if (!res.ok) throw new Error('Failed to fetch connectivity status');
    return res.json();
  },

  async simulateConnectivity(state: ConnectionState, reason?: string): Promise<ConnectivityStatus> {
    const res = await fetch(`${API_BASE}/system/connectivity/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ state, reason: reason || 'Operator simulation' })
    });
    if (!res.ok) throw new Error('Failed to simulate connectivity transition');
    return res.json();
  },

  async getSyncStatus(): Promise<SyncStatusResponse> {
    const res = await fetch(`${API_BASE}/sync/status`);
    if (!res.ok) throw new Error('Failed to fetch synchronization status');
    return res.json();
  },

  async getSyncQueue(statusFilter?: string, limit: number = 100): Promise<SyncQueueItem[]> {
    const params = new URLSearchParams();
    if (statusFilter) params.append('status', statusFilter);
    params.append('limit', String(limit));
    const res = await fetch(`${API_BASE}/sync/queue?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch sync queue items');
    return res.json();
  },

  async startSync(force: boolean = false): Promise<{ status: string; items_synced: number; items_failed: number; duration_ms: number }> {
    const res = await fetch(`${API_BASE}/sync/start?force=${force}`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to initiate synchronization');
    return res.json();
  },

  async retrySyncItem(itemId: number): Promise<SyncRetryResult> {
    const res = await fetch(`${API_BASE}/sync/retry/${itemId}`, { method: 'POST' });
    if (!res.ok) throw new Error(`Failed to retry item ${itemId}`);
    return res.json();
  },

  // --- Phase 9: On-Device & Federated Learning APIs ---

  async getModels(statusFilter?: string): Promise<ModelVersion[]> {
    const params = new URLSearchParams();
    if (statusFilter) params.append('status', statusFilter);
    const res = await fetch(`${API_BASE}/models?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch models from registry');
    return res.json();
  },

  async getActiveModel(): Promise<ModelVersion> {
    const res = await fetch(`${API_BASE}/models/active`);
    if (!res.ok) throw new Error('Failed to fetch active production model');
    return res.json();
  },

  async getCandidateModels(): Promise<ModelVersion[]> {
    const res = await fetch(`${API_BASE}/models/candidates`);
    if (!res.ok) throw new Error('Failed to fetch candidate models');
    return res.json();
  },

  async getModel(modelId: string): Promise<ModelVersion> {
    const res = await fetch(`${API_BASE}/models/${modelId}`);
    if (!res.ok) throw new Error(`Failed to fetch model ${modelId}`);
    return res.json();
  },

  async getModelAudit(modelId: string): Promise<ModelAuditLog[]> {
    const res = await fetch(`${API_BASE}/models/${modelId}/audit`);
    if (!res.ok) throw new Error(`Failed to fetch audit trail for ${modelId}`);
    return res.json();
  },

  async validateCandidateModel(modelId: string): Promise<ModelValidationResult> {
    const res = await fetch(`${API_BASE}/models/${modelId}/validate`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to validate candidate model ${modelId}`);
    }
    return res.json();
  },

  async approveModel(
    modelId: string,
    operatorId: string = 'OP-9402',
    role: string = 'SUPERVISOR',
    notes?: string
  ): Promise<ModelVersion> {
    const res = await fetch(`${API_BASE}/models/${modelId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ operator_id: operatorId, role, notes })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to approve model ${modelId}`);
    }
    return res.json();
  },

  async rejectModel(
    modelId: string,
    operatorId: string = 'OP-9402',
    role: string = 'SUPERVISOR',
    notes?: string
  ): Promise<ModelVersion> {
    const res = await fetch(`${API_BASE}/models/${modelId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ operator_id: operatorId, role, notes })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to reject model ${modelId}`);
    }
    return res.json();
  },

  async deployModel(
    modelId: string,
    operatorId: string = 'OP-9402',
    role: string = 'ADMIN',
    notes?: string
  ): Promise<ModelVersion> {
    const res = await fetch(`${API_BASE}/models/${modelId}/deploy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ operator_id: operatorId, role, notes })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to deploy model ${modelId}`);
    }
    return res.json();
  },

  async rollbackModel(
    operatorId: string = 'OP-9402',
    role: string = 'ADMIN',
    reason: string = 'Operational regression detected'
  ): Promise<any> {
    const res = await fetch(`${API_BASE}/models/rollback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ operator_id: operatorId, role, reason })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to rollback model');
    }
    return res.json();
  },

  async verifyModelIntegrity(modelId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/models/${modelId}/verify-integrity`, { method: 'POST' });
    if (!res.ok) throw new Error(`Failed to verify integrity for ${modelId}`);
    return res.json();
  },

  async getTrainingStatus(): Promise<LocalTrainingStatus> {
    const res = await fetch(`${API_BASE}/training/status`);
    if (!res.ok) throw new Error('Failed to fetch training status');
    return res.json();
  },

  async startLocalTraining(payload: {
    epochs?: number;
    batch_size?: number;
    learning_rate?: number;
    simulation_mode?: boolean;
    operator_id?: string;
    role?: string;
  } = {}): Promise<TrainingRun> {
    const res = await fetch(`${API_BASE}/training/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        epochs: payload.epochs || 5,
        batch_size: payload.batch_size || 16,
        learning_rate: payload.learning_rate || 0.001,
        simulation_mode: payload.simulation_mode || false,
        operator_id: payload.operator_id || 'OP-9402',
        role: payload.role || 'ADMIN'
      })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to start local training');
    }
    return res.json();
  },

  async getTrainingSamples(statusFilter?: string, limit: number = 100): Promise<TrainingSample[]> {
    const params = new URLSearchParams();
    if (statusFilter) params.append('status', statusFilter);
    params.append('limit', String(limit));
    const res = await fetch(`${API_BASE}/training/samples?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch training samples');
    return res.json();
  },

  async approveTrainingSample(
    sampleId: string,
    operatorId: string = 'OP-9402',
    role: string = 'OPERATOR'
  ): Promise<TrainingSample> {
    const res = await fetch(`${API_BASE}/training/samples/${sampleId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'APPROVE', operator_id: operatorId, role })
    });
    if (!res.ok) throw new Error(`Failed to approve sample ${sampleId}`);
    return res.json();
  },

  async rejectTrainingSample(
    sampleId: string,
    operatorId: string = 'OP-9402',
    role: string = 'OPERATOR'
  ): Promise<TrainingSample> {
    const res = await fetch(`${API_BASE}/training/samples/${sampleId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'REJECT', operator_id: operatorId, role })
    });
    if (!res.ok) throw new Error(`Failed to reject sample ${sampleId}`);
    return res.json();
  },

  async relabelTrainingSample(
    sampleId: string,
    correctedLabel: string,
    operatorId: string = 'OP-9402',
    role: string = 'OPERATOR'
  ): Promise<TrainingSample> {
    const res = await fetch(`${API_BASE}/training/samples/${sampleId}/relabel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'RELABEL', corrected_label: correctedLabel, operator_id: operatorId, role })
    });
    if (!res.ok) throw new Error(`Failed to relabel sample ${sampleId}`);
    return res.json();
  },

  async getFederatedRounds(): Promise<FederatedRound[]> {
    const res = await fetch(`${API_BASE}/federated/rounds`);
    if (!res.ok) throw new Error('Failed to fetch federated rounds');
    return res.json();
  },

  async createFederatedRound(baseVersion?: string, participants?: string[]): Promise<FederatedRound> {
    const res = await fetch(`${API_BASE}/federated/rounds`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        base_model_version: baseVersion,
        participating_edges: participants || ['EDGE-SECTOR-A-01', 'EDGE-SECTOR-A-02', 'EDGE-SECTOR-B-01']
      })
    });
    if (!res.ok) throw new Error('Failed to create federated round');
    return res.json();
  },

  async aggregateFederatedRound(roundId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/federated/rounds/${roundId}/aggregate`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to aggregate round ${roundId}`);
    }
    return res.json();
  },

  async getPrivacyStatus(): Promise<PrivacyStatus> {
    const res = await fetch(`${API_BASE}/federated/privacy`);
    if (!res.ok) throw new Error('Failed to fetch privacy telemetry');
    return res.json();
  },

  async runPhase9Demo(): Promise<any> {
    const res = await fetch(`${API_BASE}/demo/scenario/9`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to run Phase 9 demo');
    }
    return res.json();
  },

  async getDemoStatus(): Promise<any> {
    const res = await fetch(`${API_BASE}/demo/status`);
    if (!res.ok) throw new Error('Failed to fetch demo status');
    return res.json();
  },

  async runHeroDemo(): Promise<any> {
    const res = await fetch(`${API_BASE}/demo/hero-scenario`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to run Hero Demo');
    }
    return res.json();
  },

  async executeDemoStep(stepName: string): Promise<any> {
    const res = await fetch(`${API_BASE}/demo/step/${stepName}`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to execute step ${stepName}`);
    }
    return res.json();
  },

  getPreviewUrl(id: string, annotated: boolean = true): string {
    return `${API_BASE}/cameras/${id}/preview?annotated=${annotated}&t=${Date.now()}`;
  },

  getSnapshotUrl(id: string): string {
    return `${API_BASE}/cameras/${id}/snapshot?t=${Date.now()}`;
  }
};
