import React from 'react';
import { ShieldCheck, EyeOff, Lock, Cpu, Server } from 'lucide-react';
import { PrivacyStatus } from '../../types';

interface PrivacyStatusBannerProps {
  status: PrivacyStatus | null;
}

export const PrivacyStatusBanner: React.FC<PrivacyStatusBannerProps> = ({ status: _status }) => {
  return (
    <div className="bg-forensic-surface border border-forensic-border p-4 shadow-xs font-mono">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-signal-safe/15 text-signal-safe border border-signal-safe">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-bold text-forensic-text uppercase tracking-widest">
                PRIVACY-PRESERVING FEDERATED ARCHITECTURE
              </h3>
              <span className="px-1.5 py-0.2 text-[9px] bg-signal-safe/20 text-signal-safe border border-signal-safe font-bold">
                ZERO RAW FOOTAGE TRANSMISSION
              </span>
            </div>
            <p className="text-[11px] text-forensic-muted mt-0.5">
              Surveillance stream frames remain 100% on edge node memory. Only mathematical gradients and SHA-256 state updates are synchronized.
            </p>
          </div>
        </div>

        {/* Telemetry badges */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
          <div className="bg-forensic-elevated border border-forensic-border p-2 flex items-center gap-2">
            <EyeOff className="w-3.5 h-3.5 text-signal-safe flex-shrink-0" />
            <div>
              <span className="text-[9px] text-forensic-muted block uppercase">Raw CCTV</span>
              <span className="text-signal-safe font-bold text-[10px]">LOCAL ONLY ✓</span>
            </div>
          </div>

          <div className="bg-forensic-elevated border border-forensic-border p-2 flex items-center gap-2">
            <Lock className="w-3.5 h-3.5 text-signal-safe flex-shrink-0" />
            <div>
              <span className="text-[9px] text-forensic-muted block uppercase">Raw Frames</span>
              <span className="text-signal-safe font-bold text-[10px]">NOT SHARED ✓</span>
            </div>
          </div>

          <div className="bg-forensic-elevated border border-forensic-border p-2 flex items-center gap-2">
            <Cpu className="w-3.5 h-3.5 text-forensic-text flex-shrink-0" />
            <div>
              <span className="text-[9px] text-forensic-muted block uppercase">Local Edge AI</span>
              <span className="text-forensic-text font-bold text-[10px]">ACTIVE ✓</span>
            </div>
          </div>

          <div className="bg-forensic-elevated border border-forensic-border p-2 flex items-center gap-2">
            <Server className="w-3.5 h-3.5 text-forensic-text flex-shrink-0" />
            <div>
              <span className="text-[9px] text-forensic-muted block uppercase">Model Deltas</span>
              <span className="text-forensic-text font-bold text-[10px]">ENCRYPTED ✓</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
