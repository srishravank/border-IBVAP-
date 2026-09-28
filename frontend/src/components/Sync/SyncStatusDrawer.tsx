import React, { useState, useEffect } from 'react';
import {
  X,
  RefreshCw,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Send,
  HardDrive,
  ShieldCheck,
  RotateCcw,
  Code
} from 'lucide-react';
import {
  SyncStatusResponse,
  SyncQueueItem,
  ConnectivityStatus
} from '../../types';
import { api } from '../../services/api';

interface SyncStatusDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  connectivity: ConnectivityStatus | null;
  onRefreshParent?: () => void;
}

export const SyncStatusDrawer: React.FC<SyncStatusDrawerProps> = ({
  isOpen,
  onClose,
  connectivity,
  onRefreshParent,
}) => {
  const [syncStatus, setSyncStatus] = useState<SyncStatusResponse | null>(null);
  const [queueItems, setQueueItems] = useState<SyncQueueItem[]>([]);
  const [selectedFilter, setSelectedFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState<boolean>(false);
  const [syncing, setSyncing] = useState<boolean>(false);
  const [selectedPayload, setSelectedPayload] = useState<{ id: number; key: string; payload: any } | null>(null);

  const fetchSyncData = async () => {
    try {
      setLoading(true);
      const statusRes = await api.getSyncStatus();
      setSyncStatus(statusRes);
      const itemsRes = await api.getSyncQueue(selectedFilter === 'ALL' ? undefined : selectedFilter, 100);
      setQueueItems(itemsRes);
    } catch (err) {
      console.error('Failed to fetch sync status and queue', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchSyncData();
    }
  }, [isOpen, selectedFilter]);

  if (!isOpen) return null;

  const handleStartSync = async () => {
    try {
      setSyncing(true);
      await api.startSync(true);
      await fetchSyncData();
      if (onRefreshParent) onRefreshParent();
    } catch (err: any) {
      alert(err.message || 'Failed to trigger synchronization');
    } finally {
      setSyncing(false);
    }
  };

  const handleRetryItem = async (itemId: number) => {
    try {
      await api.retrySyncItem(itemId);
      await fetchSyncData();
      if (onRefreshParent) onRefreshParent();
    } catch (err: any) {
      alert(err.message || `Failed to retry item ${itemId}`);
    }
  };

  const summary = syncStatus?.summary;
  const isOnline = connectivity?.state === 'ONLINE' || connectivity?.state === 'SYNCING';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-forensic-surface border border-forensic-border rounded max-w-5xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden font-mono">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-forensic-border bg-forensic-elevated">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded bg-forensic-bg border border-forensic-border text-forensic-text">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xs font-bold text-forensic-text uppercase tracking-widest">Durable Synchronization Queue</h3>
                <span className="text-xs px-2 py-0.5 rounded bg-forensic-bg text-forensic-text border border-forensic-border">
                  {connectivity?.edge_id || 'EDGE-SECTOR-A-01'}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded font-bold uppercase border ${
                  isOnline
                    ? 'bg-[#C7FF3D]/10 text-emerald-800 dark:text-[#C7FF3D] border-emerald-500/40'
                    : 'bg-rose-500/10 text-[#FF4D4D] border-rose-500/40'
                }`}>
                  {connectivity?.state || 'ONLINE'}
                </span>
              </div>
              <p className="text-xs text-forensic-muted mt-0.5">
                Local-first queue with priority scheduling, exponential backoff retries, and duplicate prevention.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleStartSync}
              disabled={syncing}
              className="px-3.5 py-1.5 rounded bg-[#171717] dark:bg-[#F4F1E8] text-[#F4F1E8] dark:text-[#171717] hover:opacity-90 disabled:opacity-50 text-xs font-bold flex items-center gap-1.5 transition shadow-sm cursor-pointer"
            >
              <Send className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
              <span>{syncing ? 'SYNCING...' : 'SYNC QUEUE NOW'}</span>
            </button>
            <button
              onClick={fetchSyncData}
              disabled={loading}
              className="p-1.5 rounded bg-forensic-surface hover:bg-forensic-bg text-forensic-muted hover:text-forensic-text border border-forensic-border transition"
              title="Refresh Queue"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded text-forensic-muted hover:text-forensic-text hover:bg-forensic-bg transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Summary Metric Cards */}
        <div className="bg-forensic-bg px-6 py-4 border-b border-forensic-border grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
          <div className="p-3 bg-forensic-surface rounded border border-forensic-border">
            <span className="text-forensic-muted text-[10px] uppercase block font-bold">PENDING SYNC</span>
            <span className="text-lg font-bold text-[#F5A623]">{summary?.pending_count || 0}</span>
          </div>
          <div className="p-3 bg-forensic-surface rounded border border-forensic-border">
            <span className="text-forensic-muted text-[10px] uppercase block font-bold">SYNCHRONIZED</span>
            <span className="text-lg font-bold text-emerald-800 dark:text-[#C7FF3D]">{summary?.synced_count || 0}</span>
          </div>
          <div className="p-3 bg-forensic-surface rounded border border-forensic-border">
            <span className="text-forensic-muted text-[10px] uppercase block font-bold">FAILED / RETRY</span>
            <span className="text-lg font-bold text-[#FF4D4D]">
              {(summary?.failed_count || 0) + (summary?.retry_pending_count || 0)}
            </span>
          </div>
          <div className="p-3 bg-forensic-surface rounded border border-forensic-border">
            <span className="text-forensic-muted text-[10px] uppercase block font-bold">EVIDENCE ANCHORS</span>
            <span className="text-lg font-bold text-forensic-text">{summary?.evidence_pending_count || 0}</span>
          </div>
          <div className="p-3 bg-forensic-surface rounded border border-forensic-border">
            <span className="text-forensic-muted text-[10px] uppercase block font-bold">STORAGE USAGE</span>
            <span className="text-xs font-bold text-forensic-text block mt-1 truncate">
              {((summary?.storage_used_bytes || 0) / (1024 * 1024)).toFixed(1)} MB / 5 GB
            </span>
          </div>
        </div>

        {/* Filter Tab Bar */}
        <div className="px-6 py-2 border-b border-forensic-border bg-forensic-elevated flex items-center justify-between text-xs overflow-x-auto">
          <div className="flex items-center gap-2">
            {['ALL', 'PENDING', 'SYNCED', 'FAILED', 'RETRY_PENDING'].map((f) => (
              <button
                key={f}
                onClick={() => setSelectedFilter(f)}
                className={`px-2.5 py-1 rounded text-xs font-bold transition cursor-pointer ${
                  selectedFilter === f
                    ? 'bg-[#171717] dark:bg-[#F4F1E8] text-[#F4F1E8] dark:text-[#171717] shadow-sm'
                    : 'bg-forensic-surface text-forensic-muted hover:text-forensic-text border border-forensic-border'
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          <span className="text-forensic-muted text-[10px]">
            Last Successful Sync: {summary?.last_successful_sync ? new Date(summary.last_successful_sync).toLocaleTimeString() : 'N/A'}
          </span>
        </div>

        {/* Queue Items Table */}
        <div className="flex-1 overflow-y-auto p-6 space-y-2.5 bg-forensic-bg">
          {queueItems.length === 0 ? (
            <div className="text-center py-12 text-forensic-muted text-xs">
              <Layers className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <span>No queue items matching filter &apos;{selectedFilter}&apos;</span>
            </div>
          ) : (
            queueItems.map((item) => {
              const isP1 = item.priority === 1;
              const isP2 = item.priority === 2;
              const isSynced = item.status === 'SYNCED';
              const isFailed = item.status === 'FAILED';
              const isRetry = item.status === 'RETRY_PENDING';

              return (
                <div
                  key={item.id}
                  className="p-3.5 bg-forensic-surface rounded border border-forensic-border flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs hover:border-forensic-text transition"
                >
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        isP1
                          ? 'bg-rose-500/10 text-[#FF4D4D] border border-rose-500/30'
                          : isP2
                          ? 'bg-amber-500/10 text-[#F5A623] border border-amber-500/30'
                          : 'bg-forensic-bg text-forensic-muted border border-forensic-border'
                      }`}>
                        P{item.priority}
                      </span>
                      <span className="font-bold text-forensic-text">{item.entity_type}</span>
                      <span className="text-forensic-muted text-[10px] font-mono">{item.entity_id}</span>
                      <span className="text-forensic-muted text-[10px]">• Op: {item.operation}</span>
                    </div>

                    <div className="text-forensic-muted text-[10px] flex items-center gap-3">
                      <span>Edge Created: {new Date(item.created_at).toLocaleTimeString()}</span>
                      {item.synced_at && (
                        <span className="text-emerald-800 dark:text-[#C7FF3D] font-bold">Synced: {new Date(item.synced_at).toLocaleTimeString()}</span>
                      )}
                      {item.attempt_count > 0 && (
                        <span className="text-[#F5A623] font-bold">Attempts: {item.attempt_count}</span>
                      )}
                    </div>

                    {item.error_message && (
                      <div className="text-[#FF4D4D] text-[10px] bg-rose-500/10 p-1.5 rounded border border-rose-500/30 mt-1">
                        Error: {item.error_message}
                      </div>
                    )}
                  </div>

                  {/* Actions & Status */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className={`px-2.5 py-1 rounded text-[10px] font-bold uppercase border ${
                      isSynced
                        ? 'bg-[#C7FF3D]/10 text-emerald-800 dark:text-[#C7FF3D] border-emerald-500/30'
                        : isFailed
                        ? 'bg-rose-500/10 text-[#FF4D4D] border-rose-500/30'
                        : isRetry
                        ? 'bg-amber-500/10 text-[#F5A623] border-amber-500/30 animate-pulse'
                        : 'bg-forensic-bg text-forensic-text border-forensic-border'
                    }`}>
                      {item.status}
                    </span>

                    <button
                      onClick={() => setSelectedPayload({ id: item.id, key: item.idempotency_key, payload: item.payload })}
                      className="p-1.5 rounded bg-forensic-bg hover:bg-forensic-elevated text-forensic-muted hover:text-forensic-text border border-forensic-border transition"
                      title="Inspect Payload"
                    >
                      <Code className="w-3.5 h-3.5" />
                    </button>

                    {(isFailed || isRetry) && (
                      <button
                        onClick={() => handleRetryItem(item.id)}
                        className="px-2.5 py-1 rounded bg-amber-500/10 hover:bg-amber-500/20 text-[#F5A623] border border-amber-500/30 text-[10px] font-bold flex items-center gap-1 transition cursor-pointer"
                        title="Retry Now"
                      >
                        <RotateCcw className="w-3 h-3" />
                        Retry
                      </button>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Payload Inspector Modal */}
        {selectedPayload && (
          <div className="p-4 bg-forensic-surface border-t border-forensic-border space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-forensic-text font-bold">Payload: {selectedPayload.key}</span>
              <button
                onClick={() => setSelectedPayload(null)}
                className="text-forensic-muted hover:text-forensic-text text-xs"
              >
                Close Inspector
              </button>
            </div>
            <pre className="p-3 bg-forensic-bg rounded text-forensic-text text-[10px] overflow-x-auto max-h-36 border border-forensic-border">
              {JSON.stringify(selectedPayload.payload, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};
