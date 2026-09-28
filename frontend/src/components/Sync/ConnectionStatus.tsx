import React from 'react';
import { Wifi, WifiOff, RefreshCw, Layers } from 'lucide-react';
import { ConnectivityStatus, SyncQueueSummary } from '../../types';

interface ConnectionStatusProps {
  connectivity: ConnectivityStatus | null;
  summary: SyncQueueSummary | null;
  onToggleOffline: () => void;
  onOpenSyncDrawer: () => void;
  loading?: boolean;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  connectivity,
  summary,
  onToggleOffline,
  onOpenSyncDrawer,
  loading = false,
}) => {
  const state = connectivity?.state || 'ONLINE';
  const isOffline = state === 'OFFLINE' || state === 'DEGRADED';
  const isSyncing = state === 'SYNCING';
  const isReconnecting = state === 'RECONNECTING';

  return (
    <div className="flex items-center gap-2">
      {/* Network Status Badge */}
      <div
        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-mono font-medium transition-all ${
          isOffline
            ? 'bg-rose-950/40 border-rose-500/50 text-rose-300 shadow-sm shadow-rose-950'
            : isSyncing || isReconnecting
            ? 'bg-cyan-950/40 border-cyan-500/50 text-cyan-300 animate-pulse'
            : 'bg-emerald-950/30 border-emerald-500/40 text-emerald-300'
        }`}
      >
        {isOffline ? (
          <WifiOff className="w-3.5 h-3.5 text-rose-400" />
        ) : isSyncing || isReconnecting ? (
          <RefreshCw className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
        ) : (
          <Wifi className="w-3.5 h-3.5 text-emerald-400" />
        )}

        <div className="flex items-center gap-1.5">
          <span className="font-bold tracking-wider">{state}</span>
          {connectivity?.is_simulated && (
            <span className="text-[10px] px-1 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
              SIM
            </span>
          )}
        </div>
      </div>

      {/* Sync Queue Summary Trigger */}
      <button
        onClick={onOpenSyncDrawer}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-mono text-slate-300 hover:text-slate-100 transition-colors cursor-pointer"
        title="Open Sync Status & Queue Inspector"
      >
        <Layers className="w-3.5 h-3.5 text-indigo-400" />
        <span>Queue:</span>
        <span className={`font-bold ${summary && summary.pending_count > 0 ? 'text-amber-400' : 'text-slate-400'}`}>
          {summary?.pending_count || 0}
        </span>
        {summary && summary.failed_count > 0 && (
          <span className="px-1 py-0.2 rounded bg-rose-500/20 text-rose-300 font-bold text-[10px]">
            {summary.failed_count} ERR
          </span>
        )}
      </button>

      {/* Hero Demo Toggle Button */}
      <button
        onClick={onToggleOffline}
        disabled={loading}
        className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold border transition-all cursor-pointer shadow-sm ${
          isOffline
            ? 'bg-emerald-600 hover:bg-emerald-500 text-white border-emerald-400 shadow-emerald-950/40'
            : 'bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 border-amber-500/40'
        }`}
        title={isOffline ? 'Restore Network Connectivity & Trigger Sync' : 'Simulate Network Disconnect (Local Edge Continues)'}
      >
        {loading ? (
          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
        ) : isOffline ? (
          '⚡ RESTORE CONNECTION'
        ) : (
          '🔌 SIMULATE OFFLINE'
        )}
      </button>
    </div>
  );
};
