export type CameraStatusType = 'ONLINE' | 'OFFLINE' | 'RECONNECTING' | 'FROZEN' | 'BLACK_FRAME';
export type SourceType = 'rtsp' | 'file' | 'webcam';
export type ObjectType = 'person' | 'vehicle';
export type TrackState = 'NEW' | 'ACTIVE' | 'LOST' | 'REMOVED';

export type ZoneType = 'restricted' | 'exclusion' | 'checkpoint' | 'entry_corridor';
export type ZoneSensitivity = 'low' | 'medium' | 'high';
export type SecurityEventType = 'ZONE_ENTRY' | 'ZONE_EXIT' | 'ZONE_INTRUSION' | 'CAMERA_HEALTH';
export type EventStatus = 'CANDIDATE' | 'VERIFYING' | 'CONFIRMED' | 'REJECTED' | 'EXPIRED' | 'ACKNOWLEDGED';

export interface Camera {
  camera_id: string;
  camera_name: string;
  location: string;
  source_type: SourceType;
  source: string;
  enabled: boolean;
  status: CameraStatusType;
  target_fps?: number;
  frame_width?: number;
  frame_height?: number;
  fps: number;
  actual_width?: number;
  actual_height?: number;
  total_frames_ingested: number;
  reconnect_attempts: number;
  created_at: string;
  last_seen?: string | null;
  description?: string;
  extra_config?: Record<string, any>;
}

export interface Zone {
  zone_id: string;
  camera_id: string;
  zone_name: string;
  zone_type: ZoneType;
  polygon: [number, number][];
  enabled: boolean;
  sensitivity: ZoneSensitivity;
  description?: string;
  color?: string;
  created_at: string;
}

export interface CreateZonePayload {
  camera_id: string;
  zone_name: string;
  zone_type: ZoneType;
  polygon: [number, number][];
  enabled?: boolean;
  sensitivity?: ZoneSensitivity;
  description?: string;
  color?: string;
}

export interface VerificationDetail {
  required_frames: number;
  confirmed_frames: number;
  verification_status: 'PENDING' | 'PASSED' | 'FAILED' | 'EXPIRED' | string;
  supporting_frame_ids: number[];
  average_confidence: number;
  suppression_reasons: string[];
}

export interface SecurityEvent {
  event_id: string;
  camera_id: string;
  track_id: number;
  formatted_track_id: string;
  zone_id: string;
  zone_name: string;
  event_type: SecurityEventType;
  status: EventStatus;
  created_at: string;
  confirmed_at?: string | null;
  acknowledged_at?: string | null;
  confidence: number;
  object_type: string;
  class_name: string;
  subclass?: string | null;
  bbox: [number, number, number, number];
  reference_point: [number, number];
  trajectory: [number, number][];
  verification: VerificationDetail;
  description: string;
}

export interface CandidateSummary {
  candidate_key: string;
  camera_id: string;
  track_id: number;
  zone_id: string;
  event_type: string;
  status: string;
  confirmed_frames: number;
  required_frames: number;
  progress_pct: number;
  latest_confidence: number;
  object_type: string;
  formatted_track_id: string;
}

export interface TrackedObject {
  track_id: number;
  formatted_id: string;
  camera_id: string;
  object_type: ObjectType;
  class_name: string;
  subclass?: string | null;
  confidence: number;
  bbox: [number, number, number, number];
  center: [number, number];
  trajectory: [number, number][];
  state: TrackState;
  age: number;
  time_since_update: number;
  first_seen: string;
  last_seen: string;
  frame_id: number;
}

export interface AIPerformanceStats {
  camera_id: string;
  ai_status: string;
  model_name: string;
  inference_fps: number;
  detector_time_ms: number;
  tracker_time_ms: number;
  total_pipeline_ms: number;
  total_detections: number;
  active_tracks: number;
  persons_count: number;
  vehicles_count: number;
  processed_frames: number;
  skipped_frames: number;
  last_error?: string;
}

export interface GlobalAIStatus {
  status: string;
  detector_type: string;
  model_name: string;
  model_info: Record<string, any>;
  device: string;
  active_camera_pipelines: number;
  total_active_tracks: number;
  aggregate_inference_fps: number;
  tracking_algorithm: string;
  trajectory_history_length: number;
}

export interface AIObservation {
  observation_id: string;
  camera_id: string;
  frame_id: number;
  timestamp: string;
  object: {
    track_id: number;
    formatted_id: string;
    type: string;
    class: string;
    subclass?: string | null;
    confidence: number;
    bbox: [number, number, number, number];
    center: [number, number];
  };
  trajectory: [number, number][];
  metadata?: Record<string, any>;
}

export interface CameraEvent {
  id?: number;
  event_type: string;
  camera_id: string;
  timestamp: string;
  frame_id?: number | null;
  track_id?: number | null;
  object_type?: string | null;
  confidence?: number | null;
  message?: string | null;
  details?: Record<string, any>;
}

export interface SystemHealth {
  status: string;
  system: string;
  phase: string;
  metrics: {
    total_cameras: number;
    online_cameras: number;
    offline_cameras: number;
    reconnecting_cameras: number;
    anomaly_cameras: number;
    aggregate_fps: number;
    total_frames_ingested: number;
  };
  ai?: {
    status: string;
    model_name: string;
    device: string;
    total_active_tracks: number;
    aggregate_inference_fps: number;
  };
  verification?: {
    active_verifying_candidates: number;
    confirmed_security_events: number;
  };
}

export interface CreateCameraPayload {
  camera_id: string;
  camera_name: string;
  location: string;
  source_type: SourceType;
  source: string;
  enabled?: boolean;
  target_fps?: number;
  frame_width?: number;
  frame_height?: number;
  description?: string;
  extra_config?: Record<string, any>;
}

// --- Phase 4: Cross-Camera Intelligence & Incident Graph Types ---

export interface CameraTopologyRelation {
  relation_id: string;
  source_camera: string;
  destination_camera: string;
  min_transition_seconds: number;
  max_transition_seconds: number;
  distance_meters: number;
  direction: string;
  enabled: boolean;
  description?: string;
  created_at: string;
}

export interface SubjectTrackLink {
  id: number;
  subject_id: string;
  camera_id: string;
  track_id: number;
  formatted_track_id: string;
  match_score: number;
  match_status: string;
  evidence: string[];
  first_timestamp: string;
  last_timestamp: string;
  linked_at: string;
}

export interface SubjectJourneyStep {
  sequence: number;
  camera_id: string;
  camera_name: string;
  track_id: number;
  formatted_track_id: string;
  first_seen: string;
  last_seen: string;
  match_score: number;
  match_status: string;
  evidence: string[];
  events_triggered: {
    event_id: string;
    event_type: string;
    zone_name: string;
    status: string;
    confidence: number;
    timestamp: string;
  }[];
  associated_vehicles: {
    vehicle_id: string;
    proximity_meters: number;
    timestamp: string;
    notes: string;
  }[];
}

export interface SubjectJourney {
  subject_id: string;
  object_type: string;
  first_seen: string;
  last_seen: string;
  total_cameras: number;
  cameras_sequence: string[];
  journey_steps: SubjectJourneyStep[];
}

export interface Subject {
  subject_id: string;
  object_type: string;
  status: string;
  first_seen: string;
  last_seen: string;
  initial_camera_id: string;
  initial_track_id: number;
  total_cameras_visited: number;
  created_at: string;
  track_links: SubjectTrackLink[];
}

export interface Incident {
  incident_id: string;
  subject_id: string;
  status: string;
  title: string;
  summary: string;
  created_at: string;
  updated_at: string;
  cameras_involved: string[];
  events_count: number;
  associated_vehicles_count: number;
}

export interface IncidentTimelineEntry {
  timestamp: string;
  camera_id: string;
  camera_name: string;
  entry_type: string;
  title: string;
  description: string;
  track_id: number;
  subject_id: string;
  details: Record<string, any>;
}

export interface GraphNode {
  node_id: string;
  node_type: 'SUBJECT' | 'CAMERA' | 'TRACK' | 'ZONE' | 'EVENT' | 'VEHICLE' | string;
  label: string;
  reference_id: string;
  properties: Record<string, any>;
}

export interface GraphEdge {
  edge_id: string;
  source: string;
  target: string;
  relationship: string;
  confidence: number;
  properties: Record<string, any>;
}

export interface IncidentGraphData {
  incident_id: string;
  subject_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  generated_at: string;
}

export interface MatchCandidate {
  source_camera: string;
  source_track_id: number;
  target_camera: string;
  target_track_id: number;
  object_type: string;
  match_score: number;
  match_status: string;
  time_delta_seconds: number;
  evidence: string[];
  proposed_subject_id?: string | null;
}

// --- Phase 5: Intelligence & Explainable Risk Engine Types ---

export interface RiskFactor {
  factor_id: string;
  factor_type: string;
  factor_name: string;
  contribution: number;
  confidence: number;
  evidence: string;
  source_event_ids: string[];
  metadata?: Record<string, any>;
  is_available: boolean;
}

export interface EvidenceChecklistItem {
  factor_type: string;
  factor_name: string;
  fact: string;
  assessment: string;
  contribution: number;
  confidence: number;
  source_events: string[];
}

export interface RiskAssessment {
  assessment_id: string;
  incident_id: string;
  subject_id: string;
  score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
  confidence: number;
  config_version: string;
  explanation: string;
  factors: RiskFactor[];
  evidence_checklist: EvidenceChecklistItem[];
  created_at: string;
  updated_at: string;
}

export interface RiskHistoryEntry {
  history_id: string;
  incident_id: string;
  assessment_id: string;
  score: number;
  risk_level: string;
  factors_summary: {
    type: string;
    name: string;
    contribution: number;
    evidence: string;
  }[];
  timestamp: string;
}

export interface RiskConfig {
  config_version: string;
  weights: Record<string, number>;
  thresholds: Record<string, number>;
  night_start_time: string;
  night_end_time: string;
  enabled_factors: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RiskSummary {
  total_incidents_assessed: number;
  low_risk_count: number;
  medium_risk_count: number;
  high_risk_count: number;
  average_risk_score: number;
  active_config_version: string;
  camera_risk_distribution: Record<string, string>;
}

export interface IncidentIntelligence {
  incident_id: string;
  subject_id: string;
  risk: {
    score: number;
    level: string;
    confidence: number;
    config_version: string;
  };
  factors: {
    type: string;
    name: string;
    contribution: number;
    evidence: string;
    confidence: number;
  }[];
  explanation: string;
  context: {
    cameras: string[];
    zones: string[];
    events: string[];
    vehicles: string[];
  };
  timeline: {
    event_id: string;
    camera_id: string;
    event_type: string;
    zone_name: string;
    confidence: number;
    timestamp: string;
  }[];
  journey: {
    camera_id: string;
    track_id: number;
    formatted_track_id: string;
    match_score: number;
    match_status: string;
    first_timestamp: string;
    last_timestamp: string;
  }[];
  updated_at: string;
}

// --- Phase 6: Command & Response SOC Interface Types ---

export type UserRole = 'OPERATOR' | 'SUPERVISOR' | 'INVESTIGATOR' | 'ADMIN';

export interface DashboardSummary {
  total_cameras: number;
  online_cameras: number;
  offline_cameras: number;
  degraded_cameras: number;
  alert_cameras: number;
  total_incidents: number;
  active_incidents: number;
  critical_risk_incidents: number;
  high_risk_incidents: number;
  medium_risk_incidents: number;
  low_risk_incidents: number;
  closed_incidents: number;
  sectors_count: number;
  sectors_with_alerts: number;
  active_tracks_count: number;
  system_status: string;
  current_time: string;
}

export interface SectorRisk {
  sector_id: string;
  sector_name: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
  highest_score: number;
  active_incidents_count: number;
  cameras: string[];
  cameras_count: number;
  alert_active: boolean;
  summary: string;
}

export interface RecommendedCamera {
  camera_id: string;
  camera_name: string;
  sector: string;
  reason: string;
  confidence: number;
  transition_time_estimate_sec: number;
  distance_meters: number;
  direction: string;
  is_online: boolean;
}

export interface RecommendedCameraResponse {
  incident_id: string;
  subject_id: string;
  current_camera_id: string;
  recommended_cameras: RecommendedCamera[];
}

export interface OperatorAction {
  action_id: string;
  incident_id: string;
  operator_id: string;
  role: string;
  action: string;
  notes?: string | null;
  metadata?: Record<string, any>;
  timestamp: string;
}

export interface IncidentNote {
  note_id: string;
  incident_id: string;
  operator_id: string;
  role: string;
  note: string;
  timestamp: string;
}

export interface LifecycleStage {
  stage_name: string;
  display_name: string;
  description: string;
  is_completed: boolean;
  is_current: boolean;
  completed_at?: string | null;
  completed_by?: string | null;
  details?: string | null;
}

export interface IncidentLifecycle {
  incident_id: string;
  subject_id: string;
  current_status: string;
  stages: LifecycleStage[];
  allowed_transitions: string[];
  created_at: string;
  updated_at: string;
}

export interface IncidentNarrative {
  incident_id: string;
  subject_id: string;
  narrative_title: string;
  summary: string;
  timeline_narrative: string[];
  risk_narrative: string;
  vehicle_narrative?: string | null;
  recommendation: string;
  generated_at: string;
}

export interface CommandAlert {
  alert_id: string;
  incident_id: string;
  subject_id: string;
  title: string;
  description: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
  risk_score: number;
  camera_id: string;
  camera_name: string;
  sector_id: string;
  timestamp: string;
  requires_ack: boolean;
}

// --- Phase 7: Evidence Trust, Integrity & Blockchain Anchoring Types ---

export interface EvidenceHash {
  evidence_id: string;
  algorithm: string;
  hash_value: string;
  canonical_size_bytes: number;
  created_at: string;
}

export interface LedgerAnchor {
  transaction_id: string;
  evidence_id: string;
  incident_id: string;
  version: string;
  block_number: number;
  block_hash: string;
  previous_block_hash: string;
  anchored_hash: string;
  ledger_type: string;
  timestamp: string;
  status: string;
}

export interface EvidenceVerificationResult {
  verification_id: string;
  evidence_id: string;
  incident_id: string;
  status: 'AUTHENTIC' | 'TAMPERED' | 'NOT_FOUND' | string;
  is_authentic: boolean;
  calculated_hash: string;
  anchored_hash: string;
  algorithm: string;
  verified_at: string;
  verified_by: string;
  role: string;
  details?: Record<string, any>;
  tamper_analysis?: string | null;
}

export interface EvidenceAuditLogEntry {
  log_id: string;
  evidence_id: string;
  incident_id: string;
  action: string;
  operator_id: string;
  role: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface EvidenceInclusionSummary {
  incident_metadata: boolean;
  verified_events_count: number;
  cameras_involved_count: number;
  subject_journey_included: boolean;
  risk_assessment_included: boolean;
  operator_actions_count: number;
  operator_notes_count: number;
  media_references_count: number;
}

export interface EvidencePackage {
  evidence_id: string;
  incident_id: string;
  version: string;
  status: 'DRAFT' | 'ANCHORED' | 'VERIFIED' | 'TAMPERED' | string;
  storage_path: string;
  manifest_path: string;
  created_at: string;
  created_by: string;
  role: string;
  hash?: EvidenceHash | null;
  anchor?: LedgerAnchor | null;
  latest_verification?: EvidenceVerificationResult | null;
  inclusion_summary?: EvidenceInclusionSummary | null;
}

export interface EvidenceManifest {
  schema_version: string;
  evidence_package_id: string;
  incident_id: string;
  version: string;
  generated_at: string;
  incident: Record<string, any>;
  events: any[];
  journey: Record<string, any>;
  risk_assessment: Record<string, any>;
  operator_actions: any[];
  operator_notes: any[];
  status_history: any[];
  media_references: any[];
}

export interface LedgerBlock {
  block_number: number;
  block_hash: string;
  previous_block_hash: string;
  merkle_root: string;
  timestamp: string;
  transaction_count: number;
  transactions: any[];
}

export interface TamperDemoResult {
  status: string;
  message: string;
  evidence_id: string;
  field_modified?: string;
  original_value?: any;
  tampered_value?: any;
  tamper_instruction?: string;
}

// --- Phase 8: Offline-First Operation & Resilient Synchronization Types ---

export type ConnectionState = 'ONLINE' | 'DEGRADED' | 'OFFLINE' | 'RECONNECTING' | 'SYNCING';

export interface ConnectivityStatus {
  edge_id: string;
  state: ConnectionState;
  is_simulated: boolean;
  reason: string;
  checked_at: string;
  heartbeat_interval_seconds: number;
  central_server_url: string;
}

export interface SyncQueueItem {
  id: number;
  edge_id: string;
  idempotency_key: string;
  entity_type: string;
  entity_id: string;
  operation: string;
  priority: number;
  status: 'PENDING' | 'SYNCING' | 'SYNCED' | 'FAILED' | 'RETRY_PENDING' | string;
  payload: Record<string, any>;
  attempt_count: number;
  created_at: string;
  last_attempt_at?: string | null;
  next_retry_at?: string | null;
  synced_at?: string | null;
  error_message?: string | null;
}

export interface SyncQueueSummary {
  total_queued: number;
  pending_count: number;
  syncing_count: number;
  synced_count: number;
  failed_count: number;
  retry_pending_count: number;
  evidence_pending_count: number;
  last_successful_sync?: string | null;
  storage_used_bytes: number;
  storage_limit_bytes: number;
}

export interface SyncStatusResponse {
  edge_id: string;
  connectivity: ConnectivityStatus;
  summary: SyncQueueSummary;
  active_batch_in_progress: boolean;
  current_progress?: Record<string, any> | null;
}

export interface SyncRetryResult {
  status: string;
  message: string;
  item_id: number;
  next_status: string;
}

// --- Phase 9: On-Device / Federated Learning Types ---

export interface ModelVersion {
  model_id: string;
  version: string;
  parent_version?: string | null;
  model_type: string;
  model_hash: string;
  training_round: number;
  status: 'ACTIVE' | 'CANDIDATE' | 'ARCHIVED' | 'REJECTED' | string;
  validation_status: 'PENDING' | 'VALIDATED' | 'APPROVED' | 'REJECTED' | string;
  metrics: Record<string, any>;
  model_metadata: Record<string, any>;
  created_by: string;
  created_at: string;
  approved_by?: string | null;
  approved_at?: string | null;
  deployed_at?: string | null;
}

export interface ModelComparisonMetric {
  metric_name: string;
  active_value: number;
  candidate_value: number;
  diff: number;
  improved: boolean;
}

export interface ModelValidationResult {
  candidate_model_id: string;
  candidate_version: string;
  active_model_id: string;
  active_version: string;
  validation_status: 'PASS' | 'FAIL' | 'REVIEW_REQUIRED' | string;
  metrics_comparison: ModelComparisonMetric[];
  overall_mAP: number;
  precision: number;
  recall: number;
  f1_score: number;
  evaluated_samples: number;
  evaluated_at: string;
  recommendation: string;
}

export interface TrainingSample {
  sample_id: string;
  edge_id: string;
  camera_id: string;
  source_event_id?: string | null;
  label: string;
  label_source: 'AUTO_COLLECTED' | 'OPERATOR_REVIEWED' | 'VALIDATED' | 'REJECTED' | string;
  validation_status: 'PENDING' | 'VALIDATED' | 'REJECTED' | string;
  confidence: number;
  bbox: number[];
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  created_at: string;
  sample_metadata: Record<string, any>;
}

export interface TrainingRun {
  run_id: string;
  edge_id: string;
  base_model_version: string;
  sample_count: number;
  epochs: number;
  batch_size: number;
  learning_rate: number;
  status: 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED' | string;
  training_loss: number;
  validation_metric: number;
  metrics: {
    epoch_progress?: {
      epoch: number;
      total_epochs: number;
      loss: number;
      mAP50: number;
      precision: number;
      recall: number;
      timestamp: string;
    }[];
    final_precision?: number;
    final_recall?: number;
    simulated?: boolean;
    [key: string]: any;
  };
  error_message?: string | null;
  started_at: string;
  completed_at?: string | null;
}

export interface LocalTrainingStatus {
  edge_id: string;
  is_training: boolean;
  active_model_version: string;
  validated_samples_available: number;
  minimum_samples_required: number;
  ready_for_training: boolean;
  current_run?: TrainingRun | null;
  last_completed_run?: TrainingRun | null;
  training_device: string;
  resource_policy: Record<string, any>;
}

export interface ModelUpdate {
  update_id: string;
  edge_id: string;
  base_model_version: string;
  training_round: number;
  sample_count: number;
  training_loss: number;
  validation_metric: number;
  update_hash: string;
  status: 'CREATED' | 'QUEUED' | 'SUBMITTED' | 'REJECTED' | 'AGGREGATED' | string;
  created_at: string;
  metrics: Record<string, any>;
}

export interface FederatedRound {
  round_id: string;
  base_model_version: string;
  participants: string[];
  updates_received: number;
  aggregation_method: string;
  candidate_model_id?: string | null;
  status: 'OPEN' | 'COLLECTING' | 'AGGREGATING' | 'COMPLETED' | 'FAILED' | string;
  error_message?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface ModelAuditLog {
  log_id: string;
  model_id: string;
  action: string;
  actor: string;
  role: string;
  timestamp: string;
  log_metadata: Record<string, any>;
}

export interface PrivacyStatus {
  edge_id: string;
  raw_cctv_shared: boolean;
  raw_images_shared: boolean;
  local_training_enabled: boolean;
  model_updates_shared: boolean;
  training_metrics_shared: boolean;
  cryptographic_hashes_shared: boolean;
  audit_guarantee: string;
  last_audit_timestamp: string;
}


