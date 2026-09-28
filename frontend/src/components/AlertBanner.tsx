import React from 'react';
import { AlertTriangle, ShieldAlert, ArrowRight, Eye } from 'lucide-react';
import { CommandAlert } from '../types';

interface AlertBannerProps {
  alerts: CommandAlert[];
  onSelectIncident: (incidentId: string) => void;
  onAcknowledge: (alertId: string) => void;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({
  alerts,
  onSelectIncident,
}) => {
  if (!alerts || alerts.length === 0) return null;

  const activeAlerts = alerts.filter(a => a.risk_level === 'HIGH' || a.risk_level === 'CRITICAL');
  if (activeAlerts.length === 0) return null;

  const topAlert = activeAlerts[0];

  return (
    <div className={`border-b px-4 sm:px-6 py-2 flex items-center justify-between text-xs font-mono transition-all font-sans ${
      topAlert.risk_level === 'CRITICAL'
        ? 'bg-[#FF4D4D] border-[#FF4D4D] text-[#FFFFFF]'
        : 'bg-[#F5A623] border-[#F5A623] text-[#171717]'
    }`}>
      <div className="flex items-center gap-2.5 overflow-hidden">
        <div className={`p-1 rounded-sm flex-shrink-0 ${
          topAlert.risk_level === 'CRITICAL'
            ? 'bg-[#171717] text-[#FF4D4D]'
            : 'bg-[#171717] text-[#F5A623]'
        }`}>
          {topAlert.risk_level === 'CRITICAL' ? (
            <ShieldAlert className="w-3.5 h-3.5" />
          ) : (
            <AlertTriangle className="w-3.5 h-3.5" />
          )}
        </div>

        <div className="flex items-center gap-2 flex-wrap font-mono">
          <span className="px-1.5 py-0.2 rounded-sm bg-[#171717] text-[#FFFFFF] text-[9px] font-bold">
            {topAlert.risk_level} ALERT
          </span>
          <span className="font-bold">
            {topAlert.incident_id}:
          </span>
          <span className="truncate max-w-xl font-medium">
            {topAlert.title} — {topAlert.description}
          </span>
          <span className="text-[10px] opacity-90 hidden sm:inline">
            [{topAlert.camera_name} ({topAlert.sector_id})] • SCORE: {topAlert.risk_score}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2 flex-shrink-0 ml-4 font-mono">
        {activeAlerts.length > 1 && (
          <span className="px-1.5 py-0.2 rounded-sm bg-[#171717]/80 text-[#FFFFFF] text-[9px]">
            +{activeAlerts.length - 1} MORE
          </span>
        )}
        <button
          onClick={() => onSelectIncident(topAlert.incident_id)}
          className="px-2.5 py-0.5 rounded-sm bg-[#171717] hover:bg-[#292929] text-[#FFFFFF] text-[11px] font-bold flex items-center gap-1 transition"
        >
          <span>INSPECT</span>
          <ArrowRight className="w-3 h-3 text-[#C7FF3D]" />
        </button>
      </div>
    </div>
  );
};
