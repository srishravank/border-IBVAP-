import React, { useState, useEffect } from 'react';
import {
  Shield,
  Activity,
  Plus,
  RefreshCw,
  Layers,
  Cpu,
  Crosshair,
  Compass,
  User,
  LayoutDashboard,
  Camera,
  Flame,
  ShieldAlert,
  Lock,
  Sparkles,
  Sun,
  Moon,
  CheckCircle2,
  Terminal,
} from 'lucide-react';
import { SystemHealth, GlobalAIStatus, UserRole } from '../types';

export type DashboardViewType =
  | 'OVERVIEW'
  | 'VIDEO_MATRIX'
  | 'VIRTUAL_ZONES'
  | 'CROSS_CAMERA'
  | 'RISK_ENGINE'
  | 'INCIDENT_COMMAND'
  | 'AUDIT_FORENSICS'
  | 'FEDERATED_LEARNING'
  | 'SIMULATION_LAB';

interface HeaderProps {
  health: SystemHealth | null;
  aiStatus: GlobalAIStatus | null;
  wsConnected: boolean;
  totalZones?: number;
  confirmedEventsCount?: number;
  activeSubjectsCount?: number;
  totalIncidentsCount?: number;
  currentRole: UserRole;
  currentView: DashboardViewType;
  juryMode?: boolean;
  theme?: 'light' | 'dark';
  onToggleJuryMode?: () => void;
  onToggleTheme?: () => void;
  onViewChange: (view: DashboardViewType) => void;
  onRoleChange: (role: UserRole) => void;
  onAddCamera: () => void;
  onOpenTopology: () => void;
  onOpenRiskConfig?: () => void;
  onRefresh: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  aiStatus,
  wsConnected,
  totalZones = 0,
  confirmedEventsCount = 0,
  activeSubjectsCount = 0,
  totalIncidentsCount = 0,
  currentRole,
  currentView,
  juryMode = false,
  theme = 'light',
  onToggleJuryMode,
  onToggleTheme,
  onViewChange,
  onRoleChange,
  onAddCamera,
  onRefresh,
}) => {
  const [timeStr, setTimeStr] = useState<string>(() => new Date().toTimeString().split(' ')[0]);

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeStr(new Date().toTimeString().split(' ')[0]);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const metrics = health?.metrics || {
    total_cameras: 6,
    online_cameras: 6,
    offline_cameras: 0,
    reconnecting_cameras: 0,
    anomaly_cameras: 0,
    aggregate_fps: 0,
    total_frames_ingested: 0,
  };

  const navTabs: {
    id: DashboardViewType;
    num: string;
    label: string;
    badge?: string | number;
  }[] = [
    {
      id: 'OVERVIEW',
      num: '01',
      label: 'SOC OVERVIEW',
    },
    {
      id: 'VIDEO_MATRIX',
      num: '02',
      label: 'CAMERA MATRIX',
      badge: `${metrics.online_cameras}/${metrics.total_cameras}`,
    },
    {
      id: 'VIRTUAL_ZONES',
      num: '03',
      label: 'VIRTUAL ZONES',
      badge: totalZones,
    },
    {
      id: 'CROSS_CAMERA',
      num: '04',
      label: 'CROSS-CAMERA INTEL',
      badge: activeSubjectsCount,
    },
    {
      id: 'RISK_ENGINE',
      num: '05',
      label: 'RISK ENGINE',
    },
    {
      id: 'INCIDENT_COMMAND',
      num: '06',
      label: 'INCIDENT COMMAND',
      badge: totalIncidentsCount,
    },
    {
      id: 'AUDIT_FORENSICS',
      num: '07',
      label: 'FORENSICS / AUDIT',
    },
    {
      id: 'FEDERATED_LEARNING',
      num: '08',
      label: 'FEDERATED AI',
    },
    {
      id: 'SIMULATION_LAB',
      num: '09',
      label: 'SIMULATION LAB',
    },
  ];

  return (
    <header className="bg-[#ECE9E0] border-b border-[#D6D2C8] sticky top-0 z-30 flex flex-col font-sans transition-colors duration-150">
      {/* Top Editorial Masthead & Telemetry Strip */}
      <div className="px-4 sm:px-6 py-2.5 border-b border-[#D6D2C8] flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 bg-[#ECE9E0]">
        
        {/* Left: Intelligence Platform Masthead */}
        <div className="flex items-center gap-4">
          <div className="flex items-baseline gap-1.5 border-r border-[#D6D2C8] pr-4">
            <span className="font-mono font-black text-xl tracking-tight text-[#171717]">IBVAP</span>
            <span className="font-mono text-xs font-semibold text-[#5E5E5E]">02</span>
          </div>

          <div className="flex flex-col justify-center">
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-xs uppercase tracking-widest text-[#171717]">
                BORDER // COMMAND
              </span>
              <span className="px-1.5 py-0.2 bg-[#171717] text-[#C7FF3D] font-mono text-[9px] font-bold tracking-wider rounded-sm">
                INTELLIGENCE SYSTEM
              </span>
            </div>
            <div className="flex items-center gap-2 text-[10px] font-mono text-[#5E5E5E] mt-0.5">
              <span>SECTOR 04 TOPOLOGY</span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? 'bg-[#1A5319]' : 'bg-[#FF4D4D]'}`} />
                <span className="font-semibold text-[#171717]">{wsConnected ? 'LIVE TELEMETRY' : 'OFFLINE'}</span>
              </span>
              <span>•</span>
              <span>AI: {aiStatus?.model_name || 'YOLOv8'} ({aiStatus?.device?.toUpperCase() || 'CPU'})</span>
            </div>
          </div>
        </div>

        {/* Center/Right: Monospace System Statistics Ticker */}
        <div className="flex items-center gap-4 flex-wrap text-xs font-mono">
          <div className="flex items-center gap-3 bg-[#FFFFFF] border border-[#D6D2C8] px-3 py-1.5 rounded-sm">
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] text-[#5E5E5E]">CAMERAS</span>
              <span className="font-bold text-[#171717]">{String(metrics.online_cameras).padStart(2, '0')}</span>
            </div>
            <span className="text-[#D6D2C8]">|</span>
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] text-[#5E5E5E]">TRACKS</span>
              <span className="font-bold text-[#171717]">{String(aiStatus?.total_active_tracks ?? 12).padStart(2, '0')}</span>
            </div>
            <span className="text-[#D6D2C8]">|</span>
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] text-[#5E5E5E]">INCIDENTS</span>
              <span className={`font-bold ${totalIncidentsCount > 0 ? 'text-[#C53030]' : 'text-[#171717]'}`}>
                {String(totalIncidentsCount).padStart(2, '0')}
              </span>
            </div>
            <span className="text-[#D6D2C8]">|</span>
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] text-[#5E5E5E]">CHAIN</span>
              <span className="flex items-center gap-1 font-bold text-[#171717]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#1A5319]" />
                BLOCK 0842
              </span>
            </div>
          </div>

          <div className="hidden sm:flex items-center gap-2 bg-[#FFFFFF] border border-[#D6D2C8] px-2.5 py-1.5 rounded-sm text-[#171717] font-semibold">
            <span className="text-[10px] text-[#5E5E5E]">UTC</span>
            <span>{timeStr}</span>
          </div>

          {/* Right Action Controls */}
          <div className="flex items-center gap-1.5">
            {/* Operator Role */}
            <div className="flex items-center gap-1 bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm px-2 py-1 text-xs">
              <span className="text-[9px] text-[#5E5E5E] font-semibold">ROLE:</span>
              <select
                value={currentRole}
                onChange={(e) => onRoleChange(e.target.value as UserRole)}
                className="bg-transparent text-[#171717] font-mono text-xs font-bold focus:outline-none cursor-pointer border-none p-0"
              >
                <option value="OPERATOR">OPERATOR</option>
                <option value="SUPERVISOR">SUPERVISOR</option>
                <option value="INVESTIGATOR">INVESTIGATOR</option>
                <option value="ADMIN">ADMIN</option>
              </select>
            </div>

            {/* Refresh */}
            <button
              onClick={onRefresh}
              className="p-1.5 bg-[#FFFFFF] hover:bg-[#F4F1E8] text-[#171717] border border-[#D6D2C8] rounded-sm transition"
              title="Refresh Telemetry"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>

            {/* Theme Toggle */}
            {onToggleTheme && (
              <button
                onClick={onToggleTheme}
                className="p-1.5 bg-[#FFFFFF] hover:bg-[#F4F1E8] text-[#171717] border border-[#D6D2C8] rounded-sm transition"
                title={`Switch Theme (Current: ${theme})`}
              >
                {theme === 'light' ? <Moon className="w-3.5 h-3.5" /> : <Sun className="w-3.5 h-3.5" />}
              </button>
            )}

            {/* Jury Mode Toggle */}
            {onToggleJuryMode && (
              <button
                onClick={onToggleJuryMode}
                className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono font-bold rounded-sm border transition ${
                  juryMode
                    ? 'bg-[#171717] text-[#C7FF3D] border-[#171717]'
                    : 'bg-[#FFFFFF] text-[#5E5E5E] border-[#D6D2C8] hover:text-[#171717]'
                }`}
                title="Toggle Jury Presentation Flow"
              >
                <Sparkles className="w-3 h-3 text-[#C7FF3D]" />
                <span>{juryMode ? 'JURY: ACTIVE' : 'JURY MODE'}</span>
              </button>
            )}

            {/* Add Camera */}
            <button
              onClick={onAddCamera}
              className="flex items-center gap-1 px-2.5 py-1 bg-[#171717] hover:bg-[#292929] text-[#F4F1E8] text-xs font-mono font-semibold rounded-sm transition"
            >
              <Plus className="w-3 h-3 text-[#C7FF3D]" />
              <span>ADD CAM</span>
            </button>
          </div>
        </div>
      </div>

      {/* Editorial Minimal Navigation Tabs */}
      <div className="px-4 sm:px-6 bg-[#F4F1E8] flex items-center gap-1 overflow-x-auto border-b border-[#D6D2C8]">
        {navTabs.map((tab) => {
          const isActive = currentView === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => onViewChange(tab.id)}
              className={`flex items-center gap-2 py-2.5 px-3 text-xs font-mono transition flex-shrink-0 relative border-b-2 ${
                isActive
                  ? 'border-[#171717] text-[#171717] font-bold bg-[#ECE9E0]/60'
                  : 'border-transparent text-[#5E5E5E] hover:text-[#171717] hover:bg-[#ECE9E0]/40 font-medium'
              }`}
            >
              <span className={`text-[10px] ${isActive ? 'text-[#171717] font-bold' : 'text-[#8A877E]'}`}>
                {tab.num}
              </span>
              <span>{tab.label}</span>

              {tab.badge !== undefined && (
                <span
                  className={`px-1.5 py-0.2 text-[9px] font-mono font-bold rounded-sm ${
                    isActive
                      ? 'bg-[#171717] text-[#C7FF3D]'
                      : 'bg-[#ECE9E0] text-[#5E5E5E] border border-[#D6D2C8]'
                  }`}
                >
                  {tab.badge}
                </span>
              )}

              {isActive && (
                <span className="w-1.5 h-1.5 rounded-full bg-[#C7FF3D] border border-[#171717]" />
              )}
            </button>
          );
        })}
      </div>
    </header>
  );
};
