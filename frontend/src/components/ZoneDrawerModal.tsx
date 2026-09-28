import React, { useState, useEffect, useRef } from 'react';
import {
  X,
  ShieldAlert,
  Plus,
  Trash2,
  CheckCircle2,
  RotateCcw,
  Undo2,
  Sparkles,
  Layers,
  Crosshair,
  Check,
  MousePointer
} from 'lucide-react';
import { Zone, CreateZonePayload, ZoneType, ZoneSensitivity, Camera } from '../types';
import { api } from '../services/api';

interface ZoneDrawerModalProps {
  cameraId: string | null;
  cameras: Camera[];
  onClose: () => void;
  onZoneUpdated: () => void;
}

export const ZoneDrawerModal: React.FC<ZoneDrawerModalProps> = ({
  cameraId,
  cameras,
  onClose,
  onZoneUpdated,
}) => {
  const [selectedCam, setSelectedCam] = useState<string>(
    cameraId || (cameras[0]?.camera_id ?? 'CAM-01')
  );
  const [existingZones, setExistingZones] = useState<Zone[]>([]);
  const [polygonPoints, setPolygonPoints] = useState<[number, number][]>([]);
  const [mousePos, setMousePos] = useState<{ x: number; y: number } | null>(null);

  const [zoneName, setZoneName] = useState('Sector Restricted Fence');
  const [zoneType, setZoneType] = useState<ZoneType>('restricted');
  const [sensitivity, setSensitivity] = useState<ZoneSensitivity>('high');
  const [color, setColor] = useState('#F43F5E');
  const [description, setDescription] = useState('Tactical border virtual fence polygon');
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [bgImage, setBgImage] = useState<HTMLImageElement | null>(null);

  // Load existing zones & camera snapshot
  useEffect(() => {
    if (!selectedCam) return;
    setError(null);
    setSuccessMsg(null);

    api.getCameraZones(selectedCam).then(setExistingZones).catch(console.error);

    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.src = api.getSnapshotUrl(selectedCam);
    img.onload = () => setBgImage(img);
    img.onerror = () => setBgImage(null);
  }, [selectedCam]);

  // Redraw canvas with background image, existing zones, current points, and rubberband preview
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 1. Draw background snapshot or tactical surveillance backdrop
    if (bgImage) {
      ctx.drawImage(bgImage, 0, 0, canvas.width, canvas.height);
    } else {
      ctx.fillStyle = '#0B0F17';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }

    // Grid lines for tactical border reticle
    ctx.strokeStyle = 'rgba(51, 65, 85, 0.35)';
    ctx.lineWidth = 1;
    for (let x = 0; x < canvas.width; x += 60) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += 60) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    // 2. Draw existing configured zones for this camera
    existingZones.forEach((zone) => {
      if (!zone.polygon || zone.polygon.length < 3) return;
      ctx.beginPath();
      ctx.moveTo(zone.polygon[0][0], zone.polygon[0][1]);
      for (let i = 1; i < zone.polygon.length; i++) {
        ctx.lineTo(zone.polygon[i][0], zone.polygon[i][1]);
      }
      ctx.closePath();

      // Shaded fill
      ctx.fillStyle = (zone.color || '#F43F5E') + '2A';
      ctx.fill();

      // Border outline
      ctx.strokeStyle = zone.color || '#F43F5E';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Zone Label Tag
      ctx.font = 'bold 12px monospace';
      ctx.fillStyle = '#0B0F17';
      const labelX = zone.polygon[0][0] + 6;
      const labelY = zone.polygon[0][1] - 8;
      ctx.fillRect(labelX - 4, labelY - 12, ctx.measureText(zone.zone_name.toUpperCase()).width + 8, 16);
      ctx.fillStyle = zone.color || '#F43F5E';
      ctx.fillText(zone.zone_name.toUpperCase(), labelX, labelY);
    });

    // 3. Draw active drawing polygon in progress
    if (polygonPoints.length > 0) {
      ctx.beginPath();
      ctx.moveTo(polygonPoints[0][0], polygonPoints[0][1]);
      for (let i = 1; i < polygonPoints.length; i++) {
        ctx.lineTo(polygonPoints[i][0], polygonPoints[i][1]);
      }

      // If at least 3 points, shade the polygon
      if (polygonPoints.length >= 3) {
        ctx.closePath();
        ctx.fillStyle = color + '3D';
        ctx.fill();
      }

      ctx.strokeStyle = color;
      ctx.lineWidth = 2.5;
      ctx.setLineDash([6, 4]);
      ctx.stroke();
      ctx.setLineDash([]);

      // 4. Rubberband connecting line from last vertex to current mouse position
      if (mousePos) {
        const lastPt = polygonPoints[polygonPoints.length - 1];
        ctx.beginPath();
        ctx.moveTo(lastPt[0], lastPt[1]);
        ctx.lineTo(mousePos.x, mousePos.y);
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.5;
        ctx.setLineDash([3, 3]);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // Draw vertex handles & numbers
      polygonPoints.forEach((pt, idx) => {
        ctx.beginPath();
        ctx.arc(pt[0], pt[1], 6, 0, Math.PI * 2);
        ctx.fillStyle = idx === 0 ? '#10B981' : '#FFFFFF';
        ctx.fill();
        ctx.strokeStyle = color;
        ctx.lineWidth = 2.5;
        ctx.stroke();

        ctx.font = 'bold 11px monospace';
        ctx.fillStyle = '#FFFFFF';
        ctx.fillText(`P${idx + 1}`, pt[0] + 9, pt[1] - 5);
      });
    }

    // 5. Draw mouse crosshair and coordinates overlay
    if (mousePos) {
      ctx.strokeStyle = 'rgba(6, 182, 212, 0.6)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(mousePos.x - 12, mousePos.y);
      ctx.lineTo(mousePos.x + 12, mousePos.y);
      ctx.moveTo(mousePos.x, mousePos.y - 12);
      ctx.lineTo(mousePos.x, mousePos.y + 12);
      ctx.stroke();

      // Small coord tag near cursor
      ctx.font = '10px monospace';
      ctx.fillStyle = '#06B6D4';
      ctx.fillText(`${mousePos.x}, ${mousePos.y}`, mousePos.x + 10, mousePos.y + 16);
    }
  }, [bgImage, existingZones, polygonPoints, mousePos, color]);

  // Coordinate conversion helper
  const getCanvasCoords = (e: React.MouseEvent<HTMLCanvasElement>): { x: number; y: number } | null => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = Math.max(0, Math.min(canvas.width, Math.round((e.clientX - rect.left) * scaleX)));
    const y = Math.max(0, Math.min(canvas.height, Math.round((e.clientY - rect.top) * scaleY)));
    return { x, y };
  };

  // Canvas Click: add vertex point
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const coords = getCanvasCoords(e);
    if (!coords) return;

    setError(null);
    setSuccessMsg(null);

    // If clicking close to starting point with >= 3 vertices, close the loop
    if (polygonPoints.length >= 3) {
      const first = polygonPoints[0];
      const dist = Math.hypot(coords.x - first[0], coords.y - first[1]);
      if (dist < 25) {
        // Auto-close loop
        return;
      }
    }

    setPolygonPoints([...polygonPoints, [coords.x, coords.y]]);
  };

  // Canvas Mouse Move
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const coords = getCanvasCoords(e);
    if (coords) setMousePos(coords);
  };

  const handleMouseLeave = () => {
    setMousePos(null);
  };

  // Undo last vertex point
  const handleUndoPoint = () => {
    if (polygonPoints.length > 0) {
      setPolygonPoints(polygonPoints.slice(0, -1));
    }
  };

  // Clear all points
  const handleClearPoints = () => {
    setPolygonPoints([]);
    setError(null);
    setSuccessMsg(null);
  };

  // Apply quick presets
  const applyPreset = (presetName: string) => {
    setError(null);
    switch (presetName) {
      case 'GATE_CORRIDOR':
        setPolygonPoints([
          [380, 180],
          [900, 180],
          [940, 680],
          [340, 680],
        ]);
        setZoneName('Sector A - Main Gate Corridor');
        setZoneType('restricted');
        setColor('#F43F5E');
        break;
      case 'NORTH_PERIMETER':
        setPolygonPoints([
          [60, 140],
          [1220, 140],
          [1220, 360],
          [60, 360],
        ]);
        setZoneName('Northern Perimeter Wire Barrier');
        setZoneType('exclusion');
        setColor('#F59E0B');
        break;
      case 'SOUTH_BARRIER':
        setPolygonPoints([
          [60, 420],
          [1220, 420],
          [1220, 680],
          [60, 680],
        ]);
        setZoneName('Southern Roadway Approach Barrier');
        setZoneType('restricted');
        setColor('#F43F5E');
        break;
      case 'FULL_PERIMETER':
        setPolygonPoints([
          [100, 100],
          [1180, 100],
          [1180, 640],
          [100, 640],
        ]);
        setZoneName('Comprehensive Border Sector Enclosure');
        setZoneType('restricted');
        setColor('#06B6D4');
        break;
      case 'LEFT_FLANK':
        setPolygonPoints([
          [50, 120],
          [550, 120],
          [500, 680],
          [50, 680],
        ]);
        setZoneName('Left Flank Checkpoint Area');
        setZoneType('checkpoint');
        setColor('#10B981');
        break;
      case 'RIGHT_FLANK':
        setPolygonPoints([
          [730, 120],
          [1230, 120],
          [1230, 680],
          [780, 680],
        ]);
        setZoneName('Right Flank Infiltration Corridor');
        setZoneType('restricted');
        setColor('#A855F7');
        break;
      default:
        break;
    }
  };

  // Save Zone
  const handleSaveZone = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (!zoneName.trim()) {
      setError('Zone Name is required (e.g. Northern Fence Line)');
      return;
    }
    if (polygonPoints.length < 3) {
      setError('A virtual fence polygon requires at least 3 vertex points on the canvas.');
      return;
    }

    try {
      setSaving(true);
      const payload: CreateZonePayload = {
        camera_id: selectedCam,
        zone_name: zoneName.trim(),
        zone_type: zoneType,
        polygon: polygonPoints,
        enabled: true,
        sensitivity: sensitivity,
        description: description.trim(),
        color: color,
      };

      await api.createZone(selectedCam, payload);
      setPolygonPoints([]);
      setZoneName('Sector Restricted Fence');
      setDescription('');
      setSuccessMsg('Virtual fence saved and activated successfully!');

      // Refresh zones
      const updated = await api.getCameraZones(selectedCam);
      setExistingZones(updated);
      onZoneUpdated();
    } catch (err: any) {
      setError(err.message || 'Failed to create virtual zone');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteZone = async (zoneId: string) => {
    if (window.confirm(`Delete virtual zone '${zoneId}'?`)) {
      try {
        await api.deleteZone(zoneId);
        const updated = await api.getCameraZones(selectedCam);
        setExistingZones(updated);
        onZoneUpdated();
      } catch (err: any) {
        setError(err.message || 'Failed to delete zone');
      }
    }
  };

  if (!cameraId) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-forensic-surface border border-forensic-border rounded w-full max-w-6xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="p-4 bg-forensic-elevated border-b border-forensic-border flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-rose-500/10 text-[#FF4D4D] rounded border border-rose-500/30">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xs font-bold text-forensic-text uppercase tracking-widest font-mono">
                VIRTUAL FENCE & POLYGON GATE CONFIGURATOR
              </h2>
              <p className="text-[11px] text-forensic-muted font-mono">
                Click on the canvas to place boundary vertices or choose a 1-click tactical preset.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Camera Selector Dropdown */}
            <div className="flex items-center gap-1.5 bg-forensic-bg border border-forensic-border rounded px-2.5 py-1">
              <span className="text-[11px] font-mono text-forensic-muted">Camera:</span>
              <select
                value={selectedCam}
                onChange={(e) => {
                  setSelectedCam(e.target.value);
                  setPolygonPoints([]);
                }}
                className="bg-transparent text-xs font-mono text-forensic-text font-bold focus:outline-none cursor-pointer"
              >
                {cameras.map((c) => (
                  <option key={c.camera_id} value={c.camera_id} className="bg-forensic-surface text-forensic-text">
                    {c.camera_id} - {c.camera_name}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 text-forensic-muted hover:text-forensic-text rounded transition hover:bg-forensic-bg"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-hidden grid grid-cols-1 lg:grid-cols-3 divide-y lg:divide-y-0 lg:divide-x divide-forensic-border bg-forensic-bg">
          {/* Interactive Canvas (Left 2 Columns) */}
          <div className="lg:col-span-2 p-4 bg-forensic-bg flex flex-col items-center justify-center space-y-3">
            {/* Presets Bar */}
            <div className="w-full flex items-center justify-between gap-2 overflow-x-auto pb-1">
              <span className="text-[11px] font-mono text-forensic-muted font-semibold flex items-center gap-1 shrink-0">
                <Sparkles className="w-3.5 h-3.5 text-[#F5A623]" />
                Quick Presets:
              </span>
              <div className="flex items-center gap-1.5 flex-wrap">
                <button
                  type="button"
                  onClick={() => applyPreset('GATE_CORRIDOR')}
                  className="px-2.5 py-1 bg-forensic-surface hover:bg-forensic-elevated border border-forensic-border text-forensic-text text-[10px] font-mono font-bold rounded transition"
                >
                  + Gate Corridor
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset('NORTH_PERIMETER')}
                  className="px-2.5 py-1 bg-forensic-surface hover:bg-forensic-elevated border border-forensic-border text-forensic-text text-[10px] font-mono font-bold rounded transition"
                >
                  + North Barrier
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset('SOUTH_BARRIER')}
                  className="px-2.5 py-1 bg-forensic-surface hover:bg-forensic-elevated border border-forensic-border text-forensic-text text-[10px] font-mono font-bold rounded transition"
                >
                  + South Road
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset('FULL_PERIMETER')}
                  className="px-2.5 py-1 bg-forensic-surface hover:bg-forensic-elevated border border-forensic-border text-forensic-text text-[10px] font-mono font-bold rounded transition"
                >
                  + Full Enclosure
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset('LEFT_FLANK')}
                  className="px-2.5 py-1 bg-forensic-surface hover:bg-forensic-elevated border border-forensic-border text-forensic-text text-[10px] font-mono font-bold rounded transition"
                >
                  + Left Flank
                </button>
              </div>
            </div>

            {/* Canvas Viewport */}
            <div className="relative w-full aspect-video max-w-[800px] border border-forensic-border rounded overflow-hidden shadow-inner cursor-crosshair bg-black">
              <canvas
                ref={canvasRef}
                width={1280}
                height={720}
                onClick={handleCanvasClick}
                onMouseMove={handleMouseMove}
                onMouseLeave={handleMouseLeave}
                className="w-full h-full object-contain block"
              />

              {/* Instructions Pill Overlay */}
              <div className="absolute bottom-2 left-2 px-2.5 py-1 bg-black/80 backdrop-blur-sm rounded text-[10px] font-mono text-white border border-white/10 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#C7FF3D] animate-pulse" />
                <span>Vertices: {polygonPoints.length}</span>
                <span className="text-neutral-500">|</span>
                <span>
                  {polygonPoints.length === 0
                    ? 'Click to start plotting'
                    : polygonPoints.length < 3
                    ? `Add ${3 - polygonPoints.length} more vertex`
                    : 'Polygon ready — Click save'}
                </span>
                {mousePos && (
                  <>
                    <span className="text-neutral-500">|</span>
                    <span className="text-[#C7FF3D]">
                      X: {mousePos.x}, Y: {mousePos.y}
                    </span>
                  </>
                )}
              </div>

              {/* Action Toolbar on Top Right */}
              <div className="absolute top-2 right-2 flex items-center gap-1.5">
                {polygonPoints.length > 0 && (
                  <>
                    <button
                      type="button"
                      onClick={handleUndoPoint}
                      className="px-2.5 py-1 bg-black/80 hover:bg-black text-white rounded text-xs font-mono flex items-center gap-1 shadow backdrop-blur-sm border border-neutral-700 transition"
                      title="Undo last vertex"
                    >
                      <Undo2 className="w-3 h-3" />
                      <span>Undo</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleClearPoints}
                      className="px-2.5 py-1 bg-rose-600/90 hover:bg-rose-600 text-white rounded text-xs font-mono flex items-center gap-1 shadow backdrop-blur-sm transition"
                      title="Clear all points"
                    >
                      <RotateCcw className="w-3 h-3" />
                      <span>Clear</span>
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Configuration Form & Zone List (Right 1 Column) */}
          <div className="p-4 overflow-y-auto max-h-[620px] space-y-4 bg-forensic-surface">
            {/* Create Zone Form */}
            <form
              onSubmit={handleSaveZone}
              className="space-y-3 bg-forensic-bg p-3.5 rounded border border-forensic-border"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold font-mono text-forensic-text uppercase flex items-center gap-1.5">
                  <Plus className="w-3.5 h-3.5 text-forensic-muted" />
                  Save Virtual Fence Zone
                </span>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                    polygonPoints.length >= 3
                      ? 'bg-[#C7FF3D]/10 text-emerald-800 dark:text-[#C7FF3D] border border-emerald-500/40'
                      : 'bg-forensic-surface text-forensic-muted border border-forensic-border'
                  }`}
                >
                  {polygonPoints.length}/3 pts
                </span>
              </div>

              {error && (
                <div className="p-2 bg-rose-500/15 border border-rose-500/40 rounded text-[#FF4D4D] text-[11px] font-mono">
                  {error}
                </div>
              )}

              {successMsg && (
                <div className="p-2 bg-emerald-500/15 border border-emerald-500/40 rounded text-emerald-800 dark:text-[#C7FF3D] text-[11px] font-mono flex items-center gap-1.5">
                  <Check className="w-3.5 h-3.5" />
                  <span>{successMsg}</span>
                </div>
              )}

              <div>
                <label className="block text-[10px] font-mono text-forensic-muted mb-1">
                  Zone Name *
                </label>
                <input
                  type="text"
                  placeholder="e.g. Restricted Gate Area"
                  value={zoneName}
                  onChange={(e) => setZoneName(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-forensic-surface border border-forensic-border rounded text-xs text-forensic-text focus:outline-none focus:border-forensic-text font-mono"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[10px] font-mono text-forensic-muted mb-1">
                    Zone Type
                  </label>
                  <select
                    value={zoneType}
                    onChange={(e) => setZoneType(e.target.value as ZoneType)}
                    className="w-full px-2 py-1.5 bg-forensic-surface border border-forensic-border rounded text-xs font-mono text-forensic-text focus:outline-none"
                  >
                    <option value="restricted">Restricted Zone</option>
                    <option value="exclusion">Exclusion Strip</option>
                    <option value="checkpoint">Checkpoint Entry</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-forensic-muted mb-1">
                    Sensitivity
                  </label>
                  <select
                    value={sensitivity}
                    onChange={(e) => setSensitivity(e.target.value as ZoneSensitivity)}
                    className="w-full px-2 py-1.5 bg-forensic-surface border border-forensic-border rounded text-xs font-mono text-forensic-text focus:outline-none"
                  >
                    <option value="high">High (3 frames)</option>
                    <option value="medium">Medium (4 frames)</option>
                    <option value="low">Low (5 frames)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[10px] font-mono text-forensic-muted mb-1">
                    Zone Color
                  </label>
                  <div className="flex items-center gap-1.5">
                    {['#FF4D4D', '#F5A623', '#171717', '#C7FF3D', '#7C3AED'].map((c) => (
                      <button
                        key={c}
                        type="button"
                        onClick={() => setColor(c)}
                        className={`w-6 h-6 rounded-full border-2 transition ${
                          color === c ? 'border-forensic-text scale-110' : 'border-transparent opacity-60'
                        }`}
                        style={{ backgroundColor: c }}
                      />
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-forensic-muted mb-1">
                    Description
                  </label>
                  <input
                    type="text"
                    placeholder="Optional notes"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="w-full px-2 py-1.5 bg-forensic-surface border border-forensic-border rounded text-xs text-forensic-text focus:outline-none font-mono"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={saving || polygonPoints.length < 3}
                className="w-full py-2 bg-[#171717] dark:bg-[#F4F1E8] text-[#F4F1E8] dark:text-[#171717] disabled:opacity-40 font-bold text-xs rounded transition shadow-sm flex items-center justify-center gap-1.5 font-mono cursor-pointer"
              >
                <ShieldAlert className="w-4 h-4" />
                <span>
                  {saving
                    ? 'Saving Virtual Fence...'
                    : polygonPoints.length < 3
                    ? `Click Canvas to Draw (${polygonPoints.length}/3 pts)`
                    : 'Activate Virtual Fence'}
                </span>
              </button>
            </form>

            {/* Configured Zones List */}
            <div className="space-y-2">
              <span className="text-xs font-mono text-forensic-muted block uppercase font-bold">
                Active Zones on {selectedCam} ({existingZones.length})
              </span>

              {existingZones.length === 0 ? (
                <div className="p-4 text-center text-xs font-mono text-forensic-muted bg-forensic-bg rounded border border-forensic-border">
                  No virtual fence zones created for this camera yet.
                </div>
              ) : (
                existingZones.map((z) => (
                  <div
                    key={z.zone_id}
                    className="p-2.5 bg-forensic-bg border border-forensic-border rounded flex items-center justify-between text-xs font-mono"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span
                        className="w-3 h-3 rounded-full shrink-0"
                        style={{ backgroundColor: z.color || '#FF4D4D' }}
                      />
                      <div className="truncate">
                        <span className="text-forensic-text font-bold block truncate">
                          {z.zone_name}
                        </span>
                        <span className="text-[10px] text-forensic-muted capitalize">
                          {z.zone_type} • {z.polygon.length} vertices
                        </span>
                      </div>
                    </div>

                    <button
                      onClick={() => handleDeleteZone(z.zone_id)}
                      className="p-1 text-forensic-muted hover:text-[#FF4D4D] hover:bg-rose-500/10 rounded transition shrink-0"
                      title="Delete Zone"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
