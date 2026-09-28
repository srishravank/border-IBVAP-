import React, { useState, useEffect, useMemo } from 'react';
import {
  X,
  Share2,
  ListOrdered,
  FileCode,
  Shield,
  Video,
  Crosshair,
  MapPin,
  ShieldAlert,
  Car,
  Activity,
  Layers,
  ChevronRight
} from 'lucide-react';
import { Incident, IncidentGraphData, IncidentTimelineEntry, GraphNode, GraphEdge } from '../types';
import { api } from '../services/api';

interface IncidentGraphModalProps {
  incidentId: string | null;
  onClose: () => void;
}

export const IncidentGraphModal: React.FC<IncidentGraphModalProps> = ({
  incidentId,
  onClose,
}) => {
  const [graphData, setGraphData] = useState<IncidentGraphData | null>(null);
  const [timeline, setTimeline] = useState<IncidentTimelineEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'GRAPH' | 'TIMELINE' | 'JSON'>('GRAPH');
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  useEffect(() => {
    if (!incidentId) {
      setGraphData(null);
      setTimeline([]);
      return;
    }

    let isMounted = true;
    setLoading(true);

    Promise.all([
      api.getIncidentGraph(incidentId).catch(() => null),
      api.getIncidentTimeline(incidentId).catch(() => []),
    ])
      .then(([gData, tData]) => {
        if (isMounted) {
          if (gData) setGraphData(gData);
          if (tData) setTimeline(tData);
        }
      })
      .catch((err) => {
        console.error('Failed to load incident graph data:', err);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [incidentId]);

  // Compute 2D node coordinates for SVG graph rendering
  const layoutNodes = useMemo(() => {
    if (!graphData || graphData.nodes.length === 0) return {};

    const coords: Record<string, { x: number; y: number }> = {};
    const center = { x: 400, y: 260 };

    // Primary subject in center
    const subjectNode = graphData.nodes.find((n) => n.node_type === 'SUBJECT');
    if (subjectNode) {
      coords[subjectNode.node_id] = { x: center.x, y: center.y };
    }

    // Categorize outer nodes by type
    const cameras = graphData.nodes.filter((n) => n.node_type === 'CAMERA');
    const tracks = graphData.nodes.filter((n) => n.node_type === 'TRACK');
    const zones = graphData.nodes.filter((n) => n.node_type === 'ZONE');
    const events = graphData.nodes.filter((n) => n.node_type === 'EVENT');
    const vehicles = graphData.nodes.filter((n) => n.node_type === 'VEHICLE');

    // Layout Cameras in top arc
    cameras.forEach((cam, idx) => {
      const angle = (Math.PI / (cameras.length + 1)) * (idx + 1) + Math.PI;
      coords[cam.node_id] = {
        x: center.x + Math.cos(angle) * 220,
        y: center.y + Math.sin(angle) * 160,
      };
    });

    // Layout Tracks just below cameras
    tracks.forEach((trk, idx) => {
      const angle = (Math.PI / (tracks.length + 1)) * (idx + 1) + Math.PI;
      coords[trk.node_id] = {
        x: center.x + Math.cos(angle) * 130,
        y: center.y + Math.sin(angle) * 90,
      };
    });

    // Layout Events & Zones in bottom arc
    const bottomNodes = [...events, ...zones];
    bottomNodes.forEach((node, idx) => {
      const angle = (Math.PI / (bottomNodes.length + 1)) * (idx + 1);
      coords[node.node_id] = {
        x: center.x + Math.cos(angle) * 200,
        y: center.y + Math.sin(angle) * 150,
      };
    });

    // Layout Vehicles to the right
    vehicles.forEach((veh, idx) => {
      coords[veh.node_id] = {
        x: center.x + 240,
        y: center.y + (idx - (vehicles.length - 1) / 2) * 80,
      };
    });

    return coords;
  }, [graphData]);

  if (!incidentId) return null;

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'SUBJECT':
        return '#171717'; // Main subject
      case 'CAMERA':
        return '#888884'; // Sensors
      case 'TRACK':
        return '#F5A623'; // Amber
      case 'ZONE':
        return '#7C3AED'; // Purple
      case 'EVENT':
        return '#FF4D4D'; // Signal threat
      case 'VEHICLE':
        return '#C7FF3D'; // Signal safe/vehicle
      default:
        return '#888884';
    }
  };

  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'SUBJECT':
        return <Shield className="w-3.5 h-3.5" />;
      case 'CAMERA':
        return <Video className="w-3.5 h-3.5" />;
      case 'TRACK':
        return <Crosshair className="w-3.5 h-3.5" />;
      case 'ZONE':
        return <MapPin className="w-3.5 h-3.5" />;
      case 'EVENT':
        return <ShieldAlert className="w-3.5 h-3.5" />;
      case 'VEHICLE':
        return <Car className="w-3.5 h-3.5" />;
      default:
        return <Activity className="w-3.5 h-3.5" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-forensic-surface border border-forensic-border rounded w-full max-w-5xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        
        {/* Modal Header */}
        <div className="p-4 bg-forensic-elevated border-b border-forensic-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-forensic-bg border border-forensic-border rounded text-forensic-text">
              <Share2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xs font-bold text-forensic-text uppercase tracking-widest font-mono">
                  CROSS-CAMERA INCIDENT GRAPH & TIMELINE
                </h2>
                <span className="px-2 py-0.5 bg-forensic-bg text-forensic-text font-mono text-[10px] rounded border border-forensic-border">
                  {incidentId}
                </span>
              </div>
              <p className="text-xs text-forensic-muted font-mono">
                Multi-sensor relationship graph: Subjects, Cameras, Tracks, Virtual Zones & Events
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* View Tabs */}
            <div className="flex items-center bg-forensic-bg rounded border border-forensic-border p-0.5">
              <button
                onClick={() => setActiveTab('GRAPH')}
                className={`px-3 py-1 rounded text-xs font-mono font-bold transition flex items-center gap-1.5 ${
                  activeTab === 'GRAPH'
                    ? 'bg-[#171717] dark:bg-[#F4F1E8] text-[#F4F1E8] dark:text-[#171717] shadow-sm'
                    : 'text-forensic-muted hover:text-forensic-text'
                }`}
              >
                <Share2 className="w-3.5 h-3.5" />
                <span>Graph</span>
              </button>
              <button
                onClick={() => setActiveTab('TIMELINE')}
                className={`px-3 py-1 rounded text-xs font-mono font-bold transition flex items-center gap-1.5 ${
                  activeTab === 'TIMELINE'
                    ? 'bg-[#171717] dark:bg-[#F4F1E8] text-[#F4F1E8] dark:text-[#171717] shadow-sm'
                    : 'text-forensic-muted hover:text-forensic-text'
                }`}
              >
                <ListOrdered className="w-3.5 h-3.5" />
                <span>Timeline ({timeline.length})</span>
              </button>
              <button
                onClick={() => setActiveTab('JSON')}
                className={`px-3 py-1 rounded text-xs font-mono font-bold transition flex items-center gap-1.5 ${
                  activeTab === 'JSON'
                    ? 'bg-[#171717] dark:bg-[#F4F1E8] text-[#F4F1E8] dark:text-[#171717] shadow-sm'
                    : 'text-forensic-muted hover:text-forensic-text'
                }`}
              >
                <FileCode className="w-3.5 h-3.5" />
                <span>JSON</span>
              </button>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 text-forensic-muted hover:text-forensic-text hover:bg-forensic-bg rounded transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-5 overflow-y-auto space-y-4 flex-1 bg-forensic-bg">
          
          {loading ? (
            <div className="p-16 text-center text-xs font-mono text-forensic-muted animate-pulse flex flex-col items-center gap-2">
              <Share2 className="w-8 h-8 animate-spin text-forensic-text" />
              <span>Generating dynamic Incident Graph and Timeline...</span>
            </div>
          ) : !graphData ? (
            <div className="p-16 text-center text-xs font-mono text-forensic-muted">
              No graph data available for incident {incidentId}.
            </div>
          ) : activeTab === 'GRAPH' ? (
            <div className="space-y-4">
              
              {/* Legend Strip */}
              <div className="flex flex-wrap items-center gap-3 p-2.5 bg-forensic-surface border border-forensic-border rounded text-xs font-mono">
                <span className="text-[10px] text-forensic-muted uppercase font-bold">Node Types:</span>
                <span className="flex items-center gap-1 text-forensic-text font-bold">
                  <span className="w-2.5 h-2.5 rounded-full bg-forensic-text" />
                  Subject ({graphData.subject_id})
                </span>
                <span className="flex items-center gap-1 text-forensic-muted">
                  <span className="w-2.5 h-2.5 rounded-full bg-neutral-500" />
                  Camera Sensor
                </span>
                <span className="flex items-center gap-1 text-[#F5A623]">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#F5A623]" />
                  Local Track
                </span>
                <span className="flex items-center gap-1 text-purple-600 dark:text-purple-400">
                  <span className="w-2.5 h-2.5 rounded-full bg-purple-500" />
                  Virtual Zone
                </span>
                <span className="flex items-center gap-1 text-[#FF4D4D]">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#FF4D4D]" />
                  Security Event
                </span>
                <span className="flex items-center gap-1 text-emerald-700 dark:text-[#C7FF3D]">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                  Associated Vehicle
                </span>
              </div>

              {/* Interactive SVG Node-Edge Canvas */}
              <div className="relative bg-forensic-surface border border-forensic-border rounded overflow-hidden aspect-[16/10] flex items-center justify-center">
                <svg className="w-full h-full" viewBox="0 0 800 520">
                  <defs>
                    <marker
                      id="arrow"
                      viewBox="0 0 10 10"
                      refX="18"
                      refY="5"
                      markerWidth="6"
                      markerHeight="6"
                      orient="auto-start-reverse"
                    >
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#888884" />
                    </marker>
                  </defs>

                  {/* Render Directed Relationship Edges */}
                  {graphData.edges.map((edge) => {
                    const src = layoutNodes[edge.source];
                    const tgt = layoutNodes[edge.target];
                    if (!src || !tgt) return null;

                    const midX = (src.x + tgt.x) / 2;
                    const midY = (src.y + tgt.y) / 2;

                    return (
                      <g key={edge.edge_id} className="group">
                        <line
                          x1={src.x}
                          y1={src.y}
                          x2={tgt.x}
                          y2={tgt.y}
                          stroke="#D6D2C8"
                          strokeWidth="2"
                          strokeDasharray={edge.relationship === 'MOVED_TO' ? '4 4' : undefined}
                          markerEnd="url(#arrow)"
                          className="transition-colors group-hover:stroke-forensic-text dark:stroke-neutral-700"
                        />
                        {/* Edge Label */}
                        <text
                          x={midX}
                          y={midY - 4}
                          fill="#888884"
                          fontSize="9"
                          fontFamily="monospace"
                          textAnchor="middle"
                          className="select-none font-mono"
                        >
                          {edge.relationship}
                        </text>
                      </g>
                    );
                  })}

                  {/* Render Graph Nodes */}
                  {graphData.nodes.map((node) => {
                    const pos = layoutNodes[node.node_id];
                    if (!pos) return null;

                    const isSelected = selectedNode?.node_id === node.node_id;
                    const color = getNodeColor(node.node_type);

                    return (
                      <g
                        key={node.node_id}
                        transform={`translate(${pos.x}, ${pos.y})`}
                        onClick={() => setSelectedNode(node)}
                        className="cursor-pointer group"
                      >
                        <circle
                          r={node.node_type === 'SUBJECT' ? 22 : 16}
                          fill={node.node_type === 'SUBJECT' ? '#171717' : '#ECE9E0'}
                          stroke={color}
                          strokeWidth={isSelected ? 3 : 2}
                          className="transition transform group-hover:scale-110 shadow-md"
                        />
                        <text
                          y={node.node_type === 'SUBJECT' ? 32 : 26}
                          fill="#171717"
                          fontSize="10"
                          fontFamily="monospace"
                          fontWeight="bold"
                          textAnchor="middle"
                          className="select-none pointer-events-none dark:fill-[#F4F1E8]"
                        >
                          {node.label}
                        </text>
                      </g>
                    );
                  })}
                </svg>

                {/* Node Detail Sidecar Overlay */}
                {selectedNode && (
                  <div className="absolute top-3 right-3 bg-forensic-surface/95 border border-forensic-border rounded p-3.5 max-w-xs text-xs font-mono shadow-2xl backdrop-blur-md">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-1.5 font-bold" style={{ color: getNodeColor(selectedNode.node_type) }}>
                        {getNodeIcon(selectedNode.node_type)}
                        <span>{selectedNode.node_type}</span>
                      </div>
                      <button
                        onClick={() => setSelectedNode(null)}
                        className="text-forensic-muted hover:text-forensic-text"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <div className="space-y-1 text-[11px] text-forensic-text">
                      <div><strong>Label:</strong> {selectedNode.label}</div>
                      <div><strong>Ref ID:</strong> {selectedNode.reference_id}</div>
                      {Object.entries(selectedNode.properties).map(([k, v]) => (
                        <div key={k} className="truncate">
                          <strong className="text-forensic-muted">{k}:</strong> {String(v)}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : activeTab === 'TIMELINE' ? (
            /* Chronological Timeline View */
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-forensic-text uppercase tracking-wider font-mono flex items-center gap-2">
                <ListOrdered className="w-4 h-4 text-forensic-muted" />
                CHRONOLOGICAL MULTI-SENSOR INCIDENT TIMELINE
              </h3>

              <div className="space-y-2">
                {timeline.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-forensic-surface border border-forensic-border rounded flex items-start justify-between gap-3 text-xs font-mono hover:border-forensic-text transition"
                  >
                    <div className="flex items-start gap-2.5">
                      <span className="w-6 h-6 rounded-full bg-forensic-bg text-forensic-text border border-forensic-border flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">
                        {idx + 1}
                      </span>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-forensic-text">{item.title}</span>
                          <span className="px-1.5 py-0.2 bg-forensic-bg text-forensic-muted text-[10px] rounded border border-forensic-border">
                            {item.camera_id}
                          </span>
                        </div>
                        <p className="text-[11px] text-forensic-muted mt-1">{item.description}</p>
                      </div>
                    </div>

                    <span className="text-[11px] text-forensic-muted shrink-0">
                      {new Date(item.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            /* Raw JSON View */
            <div className="space-y-2">
              <h3 className="text-xs font-bold text-forensic-text uppercase tracking-wider font-mono">
                SERIALIZED INCIDENT GRAPH JSON (PHASE 5 READY)
              </h3>
              <pre className="p-4 bg-forensic-surface rounded text-xs font-mono text-forensic-text overflow-x-auto max-h-[500px] border border-forensic-border">
                {JSON.stringify(graphData, null, 2)}
              </pre>
            </div>
          )}

        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-forensic-elevated border-t border-forensic-border flex items-center justify-between text-xs font-mono text-forensic-muted">
          <span>Incident Graph generated from active database models and event associations</span>
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
