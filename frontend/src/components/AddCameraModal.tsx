import React, { useState } from 'react';
import { X, Plus, Video, Server, Shield } from 'lucide-react';
import { CreateCameraPayload, SourceType } from '../types';

interface AddCameraModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: CreateCameraPayload) => Promise<void>;
}

export const AddCameraModal: React.FC<AddCameraModalProps> = ({ isOpen, onClose, onSubmit }) => {
  const [cameraId, setCameraId] = useState('');
  const [cameraName, setCameraName] = useState('');
  const [location, setLocation] = useState('');
  const [sourceType, setSourceType] = useState<SourceType>('file');
  const [source, setSource] = useState('data/videos/camera01.mp4');
  const [targetFps, setTargetFps] = useState(25.0);
  const [frameWidth, setFrameWidth] = useState(1280);
  const [frameHeight, setFrameHeight] = useState(720);
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSourceTypeChange = (type: SourceType) => {
    setSourceType(type);
    if (type === 'file') {
      setSource('data/videos/camera01.mp4');
    } else if (type === 'webcam') {
      setSource('0');
    } else if (type === 'rtsp') {
      setSource('rtsp://admin:password@192.168.1.100:554/stream1');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const cleanId = cameraId.trim().replace(/[\s\-]+/g, '-').toUpperCase();
    const cleanSource = source.trim().replace(/^["']|["']$/g, '').trim();

    if (!cleanId) {
      setError('Camera ID is required (e.g. CAM-05)');
      return;
    }
    if (!cameraName.trim()) {
      setError('Camera Name is required');
      return;
    }
    if (!cleanSource) {
      setError('Source URI / Path is required');
      return;
    }

    try {
      setLoading(true);
      await onSubmit({
        camera_id: cleanId,
        camera_name: cameraName.trim(),
        location: location.trim() || 'Border Sector Alpha',
        source_type: sourceType,
        source: cleanSource,
        enabled: true,
        target_fps: Number(targetFps) || 25.0,
        frame_width: Number(frameWidth) || 1280,
        frame_height: Number(frameHeight) || 720,
        description: description.trim(),
      });
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to register camera');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-forensic-surface border border-forensic-border rounded w-full max-w-lg shadow-2xl overflow-hidden">
        
        {/* Modal Header */}
        <div className="p-4 bg-forensic-elevated border-b border-forensic-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-forensic-bg border border-forensic-border text-forensic-text rounded">
              <Plus className="w-4 h-4" />
            </div>
            <h2 className="text-xs font-bold text-forensic-text uppercase tracking-widest font-mono">
              Register New CCTV Camera
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-forensic-muted hover:text-forensic-text rounded transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4 bg-forensic-bg">
          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded text-[#FF4D4D] text-xs font-mono">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-mono text-forensic-muted mb-1">
                Camera ID *
              </label>
              <input
                type="text"
                placeholder="e.g. CAM-05"
                value={cameraId}
                onChange={(e) => setCameraId(e.target.value)}
                className="w-full px-3 py-2 bg-forensic-surface border border-forensic-border rounded text-xs font-mono text-forensic-text focus:outline-none focus:border-forensic-text"
                required
              />
            </div>
            <div>
              <label className="block text-[11px] font-mono text-forensic-muted mb-1">
                Camera Name *
              </label>
              <input
                type="text"
                placeholder="e.g. Sector E Outpost"
                value={cameraName}
                onChange={(e) => setCameraName(e.target.value)}
                className="w-full px-3 py-2 bg-forensic-surface border border-forensic-border rounded text-xs font-mono text-forensic-text focus:outline-none focus:border-forensic-text"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-mono text-forensic-muted mb-1">
              Sector Location
            </label>
            <input
              type="text"
              placeholder="e.g. Sector E (Eastern Valley)"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full px-3 py-2 bg-forensic-surface border border-forensic-border rounded text-xs font-mono text-forensic-text focus:outline-none focus:border-forensic-text"
            />
          </div>

          {/* Source Type Selector */}
          <div>
            <label className="block text-[11px] font-mono text-forensic-muted mb-1.5">
              Source Protocol / Type *
            </label>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleSourceTypeChange('file')}
                className={`py-2 px-3 rounded border text-xs font-mono font-bold flex items-center justify-center gap-1.5 transition ${
                  sourceType === 'file'
                    ? 'bg-forensic-elevated border-forensic-text text-forensic-text shadow-sm'
                    : 'bg-forensic-surface border-forensic-border text-forensic-muted hover:text-forensic-text'
                }`}
              >
                <Video className="w-3.5 h-3.5" />
                <span>Video File</span>
              </button>

              <button
                type="button"
                onClick={() => handleSourceTypeChange('rtsp')}
                className={`py-2 px-3 rounded border text-xs font-mono font-bold flex items-center justify-center gap-1.5 transition ${
                  sourceType === 'rtsp'
                    ? 'bg-forensic-elevated border-forensic-text text-forensic-text shadow-sm'
                    : 'bg-forensic-surface border-forensic-border text-forensic-muted hover:text-forensic-text'
                }`}
              >
                <Server className="w-3.5 h-3.5" />
                <span>RTSP Stream</span>
              </button>

              <button
                type="button"
                onClick={() => handleSourceTypeChange('webcam')}
                className={`py-2 px-3 rounded border text-xs font-mono font-bold flex items-center justify-center gap-1.5 transition ${
                  sourceType === 'webcam'
                    ? 'bg-forensic-elevated border-forensic-text text-forensic-text shadow-sm'
                    : 'bg-forensic-surface border-forensic-border text-forensic-muted hover:text-forensic-text'
                }`}
              >
                <Shield className="w-3.5 h-3.5" />
                <span>Webcam</span>
              </button>
            </div>
          </div>

          {/* Source Path / URL */}
          <div>
            <label className="block text-[11px] font-mono text-forensic-muted mb-1">
              Source URI / Path *
            </label>
            <input
              type="text"
              placeholder={sourceType === 'rtsp' ? 'rtsp://user:pass@ip:port/stream' : sourceType === 'file' ? '13258882-uhd_3840_2160_30fps.mp4 or data/videos/camera01.mp4' : '0'}
              value={source}
              onChange={(e) => setSource(e.target.value.replace(/^["']|["']$/g, ''))}
              className="w-full px-3 py-2 bg-forensic-surface border border-forensic-border rounded text-xs font-mono text-forensic-text focus:outline-none focus:border-forensic-text"
              required
            />
            {sourceType === 'file' && (
              <p className="mt-1 text-[10px] text-forensic-muted font-mono">
                Tip: Enter file name (e.g. <span className="text-forensic-text font-bold">13258882-uhd_3840_2160_30fps.mp4</span>) or relative/full path without quotes.
              </p>
            )}
          </div>

          {/* Resolution & FPS */}
          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="block text-[11px] font-mono text-forensic-muted mb-1">
                Target FPS
              </label>
              <input
                type="number"
                value={targetFps}
                onChange={(e) => setTargetFps(Number(e.target.value))}
                className="w-full px-3 py-2 bg-forensic-surface border border-forensic-border rounded text-xs font-mono text-forensic-text focus:outline-none focus:border-forensic-text"
              />
            </div>
            <div>
              <label className="block text-[11px] font-mono text-forensic-muted mb-1">
                Width (px)
              </label>
              <input
                type="number"
                value={frameWidth}
                onChange={(e) => setFrameWidth(Number(e.target.value))}
                className="w-full px-3 py-2 bg-forensic-surface border border-forensic-border rounded text-xs font-mono text-forensic-text focus:outline-none focus:border-forensic-text"
              />
            </div>
            <div>
              <label className="block text-[11px] font-mono text-forensic-muted mb-1">
                Height (px)
              </label>
              <input
                type="number"
                value={frameHeight}
                onChange={(e) => setFrameHeight(Number(e.target.value))}
                className="w-full px-3 py-2 bg-forensic-surface border border-forensic-border rounded text-xs font-mono text-forensic-text focus:outline-none focus:border-forensic-text"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-mono text-forensic-muted mb-1">
              Description / Notes
            </label>
            <input
              type="text"
              placeholder="Optional notes or border sensor remarks"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 bg-forensic-surface border border-forensic-border rounded text-xs font-mono text-forensic-text focus:outline-none focus:border-forensic-text"
            />
          </div>

          {/* Actions */}
          <div className="pt-2 flex items-center justify-end gap-2 border-t border-forensic-border">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-forensic-surface hover:bg-forensic-bg text-forensic-muted hover:text-forensic-text text-xs font-mono rounded border border-forensic-border transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-[#171717] dark:bg-[#F4F1E8] text-[#F4F1E8] dark:text-[#171717] disabled:opacity-50 text-xs font-mono font-bold rounded transition shadow-sm flex items-center gap-1.5"
            >
              {loading ? 'Initializing Stream...' : 'Register Camera'}
            </button>
          </div>
        </form>

      </div>
    </div>
  );
};
