import React from 'react';
import { WifiOff, ShieldAlert, Cpu } from 'lucide-react';
import { ConnectivityStatus } from '../../types';

interface OfflineBannerProps {
  connectivity: ConnectivityStatus | null;
  pendingCount?: number;
  onRestore?: () => void;
}

export const OfflineBanner: React.FC<OfflineBannerProps> = ({
  connectivity,
  pendingCount = 0,
  onRestore,
}) => {
  const isOffline = connectivity?.state === 'OFFLINE' || connectivity?.state === 'DEGRADED';

  if (!isOffline) return null;

  return (
    <div className="bg-gradient-to-r from-rose-950/80 via-slate-900 to-amber-950/80 border-b border-rose-500/40 px-4 py-2.5 flex items-center justify-between gap-4 text-xs font-mono shadow-md animate-fade-in">
      <div className="flex items-center gap-3">
        <div className="p-1.5 rounded-lg bg-rose-500/20 border border-rose-500/40 text-rose-300">
          <WifiOff className="w-4 h-4 text-rose-400" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-rose-300 uppercase tracking-wider">OFFLINE OPERATION ACTIVE</span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              Edge Node: {connectivity?.edge_id || 'EDGE-01'}
            </span>
          </div>
          <p className="text-[11px] text-slate-300 mt-0.5 flex items-center gap-1.5 flex-wrap">
            <Cpu className="w-3 h-3 text-cyan-400 inline" />
            <span>AI CCTV Ingestion, Detection, Tracking, Risk Engine & Evidence Hashing continue locally.</span>
            <span className="text-amber-300 font-bold">({pendingCount} items queued for sync)</span>
          </p>
        </div>
      </div>

      {onRestore && (
        <button
          onClick={onRestore}
          className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-sm transition-colors flex-shrink-0 cursor-pointer"
        >
          RESTORE CONNECTION
        </button>
      )}
    </div>
  );
};
