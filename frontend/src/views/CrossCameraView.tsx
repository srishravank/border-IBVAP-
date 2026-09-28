import React, { useState, useEffect } from 'react';
import {
  Subject,
  SubjectJourney,
  CameraTopologyRelation,
  Incident,
  Camera as CameraType,
} from '../types';
import { api } from '../services/api';
import {
  Compass,
  Network,
  Share2,
  Car,
  User,
  ArrowRight,
  ShieldAlert,
  FileText,
} from 'lucide-react';

interface CrossCameraViewProps {
  subjects: Subject[];
  incidents: Incident[];
  cameras: CameraType[];
  onOpenTopology: () => void;
  onSelectIncident: (incidentId: string) => void;
  onSelectIncidentGraph: (incidentId: string) => void;
  onSelectSubjectJourney: (subjectId: string) => void;
  onRefresh: () => void;
}

export const CrossCameraView: React.FC<CrossCameraViewProps> = ({
  subjects,
  incidents,
  cameras,
  onOpenTopology,
  onSelectIncident,
  onSelectIncidentGraph,
  onSelectSubjectJourney,
  onRefresh,
}) => {
  const [activeTab, setActiveTab] = useState<'JOURNEYS' | 'TOPOLOGY' | 'REID' | 'VEHICLES'>('JOURNEYS');
  const [selectedSubjectId, setSelectedSubjectId] = useState<string | null>(
    subjects.length > 0 ? subjects[0].subject_id : null
  );
  const [selectedJourney, setSelectedJourney] = useState<SubjectJourney | null>(null);
  const [topologyRoutes, setTopologyRoutes] = useState<CameraTopologyRelation[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    const loadTopology = async () => {
      try {
        const routes = await api.getTopology().catch(() => []);
        setTopologyRoutes(routes);
      } catch (e) {
        console.error(e);
      }
    };
    loadTopology();
  }, []);

  useEffect(() => {
    if (!selectedSubjectId) {
      if (subjects.length > 0) setSelectedSubjectId(subjects[0].subject_id);
      return;
    }

    let isMounted = true;
    const loadJourney = async () => {
      try {
        setIsLoading(true);
        const j = await api.getSubjectJourney(selectedSubjectId);
        if (isMounted) setSelectedJourney(j);
      } catch (e) {
        console.error('Error fetching subject journey:', e);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };
    loadJourney();

    return () => {
      isMounted = false;
    };
  }, [selectedSubjectId, subjects]);

  return (
    <div className="space-y-4 font-sans">
      {/* Header Toolbar */}
      <div className="bg-[#ECE9E0] border border-[#D6D2C8] rounded-sm p-3.5 shadow-none flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Compass className="w-4 h-4 text-[#171717]" />
            <div>
              <h2 className="text-xs font-bold text-[#171717] uppercase tracking-wider font-mono">
                CROSS-CAMERA SPATIAL INTELLIGENCE & RE-ID
              </h2>
              <p className="text-[10px] text-[#5E5E5E] font-mono">
                MULTI-CAMERA LINKAGE • SPATIAL TOPOLOGY • VEHICLE CORRELATION
              </p>
            </div>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-2 flex-wrap font-mono text-xs">
          <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-0.5 flex items-center">
            <button
              onClick={() => setActiveTab('JOURNEYS')}
              className={`px-2.5 py-1 rounded-sm font-semibold transition text-[11px] ${
                activeTab === 'JOURNEYS'
                  ? 'bg-[#171717] text-[#C7FF3D]'
                  : 'text-[#5E5E5E] hover:text-[#171717]'
              }`}
            >
              JOURNEYS ({subjects.length})
            </button>
            <button
              onClick={() => setActiveTab('TOPOLOGY')}
              className={`px-2.5 py-1 rounded-sm font-semibold transition text-[11px] ${
                activeTab === 'TOPOLOGY'
                  ? 'bg-[#171717] text-[#C7FF3D]'
                  : 'text-[#5E5E5E] hover:text-[#171717]'
              }`}
            >
              TOPOLOGY ({topologyRoutes.length} ROUTES)
            </button>
            <button
              onClick={() => setActiveTab('REID')}
              className={`px-2.5 py-1 rounded-sm font-semibold transition text-[11px] ${
                activeTab === 'REID'
                  ? 'bg-[#171717] text-[#C7FF3D]'
                  : 'text-[#5E5E5E] hover:text-[#171717]'
              }`}
            >
              RE-ID MATRIX
            </button>
            <button
              onClick={() => setActiveTab('VEHICLES')}
              className={`px-2.5 py-1 rounded-sm font-semibold transition text-[11px] ${
                activeTab === 'VEHICLES'
                  ? 'bg-[#171717] text-[#C7FF3D]'
                  : 'text-[#5E5E5E] hover:text-[#171717]'
              }`}
            >
              VEHICLE CORRELATION
            </button>
          </div>

          <button
            onClick={onOpenTopology}
            className="flex items-center gap-1 px-3 py-1 bg-[#171717] hover:bg-[#292929] text-[#F4F1E8] rounded-sm text-xs font-mono font-semibold transition"
          >
            <Network className="w-3.5 h-3.5 text-[#C7FF3D]" />
            <span>CONFIGURE TOPOLOGY</span>
          </button>
        </div>
      </div>

      {/* Tab Views */}
      {activeTab === 'JOURNEYS' ? (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 items-start">
          {/* Left: Subjects List */}
          <div className="xl:col-span-1 space-y-3 font-mono">
            <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-3 shadow-none space-y-2.5">
              <div className="flex items-center justify-between border-b border-[#ECE9E0] pb-2">
                <span className="text-xs font-bold text-[#171717] uppercase flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5 text-[#171717]" />
                  IDENTIFIED GLOBAL SUBJECTS ({subjects.length})
                </span>
                <span className="text-[10px] text-[#5E5E5E]">MULTI-HOP RE-ID</span>
              </div>

              {subjects.length === 0 ? (
                <div className="p-8 text-center text-[#5E5E5E] text-xs flex flex-col items-center justify-center gap-1.5">
                  <Compass className="w-6 h-6 text-[#8A877E]" />
                  <span className="font-bold text-[#171717]">NO GLOBAL SUBJECTS RECORDED</span>
                  <span className="text-[10px] text-[#8A877E]">Trigger Scenario 04 or 05 in Simulation Controls.</span>
                </div>
              ) : (
                <div className="space-y-1.5">
                  {subjects.map((subj) => {
                    const isSelected = selectedSubjectId === subj.subject_id;
                    const cams = Array.from(new Set(subj.track_links.map((l) => l.camera_id)));
                    const inc = incidents.find((i) => i.subject_id === subj.subject_id);

                    return (
                      <div
                        key={subj.subject_id}
                        onClick={() => setSelectedSubjectId(subj.subject_id)}
                        className={`p-2.5 rounded-sm border transition cursor-pointer flex flex-col gap-1.5 ${
                          isSelected
                            ? 'bg-[#F4F1E8] border-[#171717] ring-1 ring-[#171717]'
                            : 'bg-[#FFFFFF] border-[#D6D2C8] hover:border-[#171717]/60'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5">
                            <span className="px-1.5 py-0.2 bg-[#171717] text-[#C7FF3D] font-bold rounded-sm text-[10px]">
                              {subj.subject_id}
                            </span>
                            <span className="text-xs font-bold text-[#171717] uppercase">
                              {subj.object_type}
                            </span>
                          </div>
                          <span className="text-[10px] text-[#5E5E5E]">
                            {new Date(subj.last_seen).toLocaleTimeString()}
                          </span>
                        </div>

                        {/* Route breadcrumbs */}
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

                        {inc && (
                          <div className="flex items-center justify-between pt-1 border-t border-[#ECE9E0]">
                            <span className="text-[9px] font-bold text-[#C53030]">
                              LINKED: {inc.incident_id}
                            </span>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onSelectIncident(inc.incident_id);
                              }}
                              className="text-[9px] font-bold text-[#171717] hover:underline flex items-center gap-1"
                            >
                              <FileText className="w-3 h-3 text-[#FF4D4D]" />
                              <span>COCKPIT</span>
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Right: Subject Journey Visualizer */}
          <div className="xl:col-span-2 space-y-4 font-mono">
            {selectedJourney ? (
              <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-4 shadow-none space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#ECE9E0] pb-2.5">
                  <div>
                    <span className="text-[10px] text-[#5E5E5E] font-bold block">
                      CROSS-CAMERA TRANSIT JOURNEY
                    </span>
                    <h3 className="text-sm font-bold text-[#171717] flex items-center gap-2">
                      <span>SUBJECT: {selectedJourney.subject_id}</span>
                      <span className="px-1.5 py-0.2 bg-[#171717] text-[#C7FF3D] rounded-sm text-[9px]">
                        {selectedJourney.total_cameras} CAMERAS IN ROUTE
                      </span>
                    </h3>
                  </div>

                  <button
                    onClick={() => onSelectSubjectJourney(selectedJourney.subject_id)}
                    className="px-2.5 py-1 bg-[#171717] hover:bg-[#292929] text-[#F4F1E8] rounded-sm text-xs font-semibold flex items-center gap-1 transition"
                  >
                    <Compass className="w-3.5 h-3.5 text-[#C7FF3D]" />
                    <span>FULL MODAL</span>
                  </button>
                </div>

                {/* Spatial Sequence Stepper */}
                <div className="relative pl-6 space-y-4 border-l-2 border-[#171717] my-3 ml-3">
                  {selectedJourney.journey_steps.map((step) => (
                    <div key={step.sequence} className="relative space-y-1.5">
                      <div className="absolute -left-[31px] top-0 w-5 h-5 rounded-full bg-[#171717] border-2 border-[#FFFFFF] flex items-center justify-center text-[9px] font-bold text-[#C7FF3D]">
                        {step.sequence}
                      </div>

                      <div className="bg-[#F4F1E8] border border-[#D6D2C8] rounded-sm p-3 space-y-1.5">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5">
                            <span className="px-1.5 py-0.2 bg-[#171717] text-[#C7FF3D] font-bold rounded-sm text-[10px]">
                              {step.camera_id}
                            </span>
                            <span className="font-bold text-xs text-[#171717]">
                              {step.camera_name}
                            </span>
                            <span className="text-[10px] text-[#5E5E5E]">
                              (TRACK #{step.track_id})
                            </span>
                          </div>

                          <span className="px-1.5 py-0.2 bg-[#171717] text-[#C7FF3D] rounded-sm text-[9px] font-bold">
                            {(step.match_score * 100).toFixed(0)}% RE-ID MATCH
                          </span>
                        </div>

                        <div className="flex items-center gap-4 text-[10px] text-[#5E5E5E]">
                          <span>FIRST SEEN: {new Date(step.first_seen).toLocaleTimeString()}</span>
                          <span>LAST SEEN: {new Date(step.last_seen).toLocaleTimeString()}</span>
                        </div>

                        {step.evidence?.length > 0 && (
                          <div className="pt-1 border-t border-[#D6D2C8] flex flex-wrap gap-1">
                            {step.evidence.map((ev, i) => (
                              <span
                                key={i}
                                className="px-1.5 py-0.2 bg-[#FFFFFF] text-[#171717] border border-[#D6D2C8] rounded-sm text-[9px]"
                              >
                                ✓ {ev}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-12 text-center text-[#5E5E5E] text-xs">
                Select a subject on the left to view spatial transit breakdown.
              </div>
            )}
          </div>
        </div>
      ) : activeTab === 'TOPOLOGY' ? (
        <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-4 space-y-3 font-mono">
          <div className="flex items-center justify-between border-b border-[#ECE9E0] pb-2">
            <span className="text-xs font-bold text-[#171717] uppercase">
              CAMERA SPATIAL TOPOLOGY & TRANSIT TIME MATRIX
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="bg-[#ECE9E0] border-b border-[#D6D2C8] text-[#5E5E5E] uppercase text-[9px] font-bold">
                  <th className="py-2 px-3">ROUTE ID</th>
                  <th className="py-2 px-3">SRC CAM</th>
                  <th className="py-2 px-3">DEST CAM</th>
                  <th className="py-2 px-3">DISTANCE</th>
                  <th className="py-2 px-3">TRANSIT TIME</th>
                  <th className="py-2 px-3">DIRECTION</th>
                  <th className="py-2 px-3">STATUS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#ECE9E0]">
                {topologyRoutes.map((r) => (
                  <tr key={r.relation_id} className="hover:bg-[#F4F1E8] transition">
                    <td className="py-2 px-3 font-bold text-[#171717]">{r.relation_id}</td>
                    <td className="py-2 px-3 font-bold text-[#171717]">{r.source_camera}</td>
                    <td className="py-2 px-3 font-bold text-[#171717]">{r.destination_camera}</td>
                    <td className="py-2 px-3 font-bold text-[#171717]">{r.distance_meters}m</td>
                    <td className="py-2 px-3 text-[#5E5E5E]">{r.min_transition_seconds}s – {r.max_transition_seconds}s</td>
                    <td className="py-2 px-3 text-[#5E5E5E] uppercase">{r.direction}</td>
                    <td className="py-2 px-3">
                      <span className="px-1.5 py-0.2 bg-[#171717] text-[#C7FF3D] rounded-sm text-[9px] font-bold">
                        ACTIVE
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : activeTab === 'REID' ? (
        <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-4 space-y-3 font-mono">
          <h3 className="text-xs font-bold text-[#171717] uppercase">
            RE-IDENTIFICATION & APPEARANCE SIMILARITY ENGINE
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="bg-[#F4F1E8] border border-[#D6D2C8] rounded-sm p-3 space-y-1">
              <span className="text-xs font-bold text-[#171717]">1. Appearance Embedding</span>
              <p className="text-[10px] text-[#5E5E5E]">Cosine distance across multi-scale feature vectors for torso, head, and clothing signatures.</p>
            </div>
            <div className="bg-[#F4F1E8] border border-[#D6D2C8] rounded-sm p-3 space-y-1">
              <span className="text-xs font-bold text-[#171717]">2. Spatial Transit Window</span>
              <p className="text-[10px] text-[#5E5E5E]">Enforces strict minimum/maximum physical travel times based on topological distance.</p>
            </div>
            <div className="bg-[#F4F1E8] border border-[#D6D2C8] rounded-sm p-3 space-y-1">
              <span className="text-xs font-bold text-[#171717]">3. Heading Alignment</span>
              <p className="text-[10px] text-[#5E5E5E]">Matches exit velocity vector on Source Camera with entry vector on Destination Camera.</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-4 space-y-3 font-mono">
          <h3 className="text-xs font-bold text-[#171717] uppercase">
            PERSON + VEHICLE MULTI-ENTITY ASSOCIATION
          </h3>
          <div className="p-6 bg-[#F4F1E8] rounded-sm border border-[#D6D2C8] flex flex-col md:flex-row items-center justify-around gap-4">
            <div className="flex items-center gap-2 bg-[#FFFFFF] p-3 rounded-sm border border-[#D6D2C8]">
              <User className="w-6 h-6 text-[#171717]" />
              <div>
                <span className="text-xs font-bold text-[#171717] block">PERSON P183</span>
                <span className="text-[9px] text-[#5E5E5E]">VELOCITY: 1.4 m/s</span>
              </div>
            </div>

            <div className="flex flex-col items-center gap-1 text-xs text-[#B45309]">
              <span className="px-1.5 py-0.2 bg-[#F5A623] text-[#171717] rounded-sm text-[9px] font-bold">
                PROXIMITY: 4.2 METERS
              </span>
              <div className="w-24 h-0.5 bg-[#D6D2C8]" />
              <span className="text-[9px] text-[#5E5E5E]">CO-PRESENCE: 28 SECONDS</span>
            </div>

            <div className="flex items-center gap-2 bg-[#FFFFFF] p-3 rounded-sm border border-[#D6D2C8]">
              <Car className="w-6 h-6 text-[#171717]" />
              <div>
                <span className="text-xs font-bold text-[#171717] block">VEHICLE V22</span>
                <span className="text-[9px] text-[#5E5E5E]">BLACK PICKUP TRUCK</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
