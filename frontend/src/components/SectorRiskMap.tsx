import React from 'react';
import { Camera, ShieldAlert, Crosshair, MapPin, ArrowRight } from 'lucide-react';
import { SectorRisk } from '../types';

interface SectorRiskMapProps {
  sectors: SectorRisk[];
  selectedSectorId: string | null;
  onSelectSector: (sectorId: string | null) => void;
  onFocusCamera?: (cameraId: string) => void;
}

export const SectorRiskMap: React.FC<SectorRiskMapProps> = ({
  sectors,
  selectedSectorId,
  onSelectSector,
  onFocusCamera,
}) => {
  const getSectorSignal = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return {
          dot: 'bg-[#FF4D4D]',
          badge: 'bg-[#FF4D4D] text-[#FFFFFF]',
          border: 'border-[#FF4D4D]',
          text: 'text-[#C53030]',
          gridCode: 'GRID 7F-A4 / CRITICAL',
        };
      case 'HIGH':
        return {
          dot: 'bg-[#F5A623]',
          badge: 'bg-[#F5A623] text-[#171717]',
          border: 'border-[#F5A623]',
          text: 'text-[#B45309]',
          gridCode: 'GRID 7F-A3 / ELEVATED',
        };
      case 'MEDIUM':
        return {
          dot: 'bg-[#F5A623]',
          badge: 'bg-[#ECE9E0] text-[#B45309] border border-[#D6D2C8]',
          border: 'border-[#D6D2C8]',
          text: 'text-[#B45309]',
          gridCode: 'GRID 7F-A2 / CAUTION',
        };
      default:
        return {
          dot: 'bg-[#C7FF3D]',
          badge: 'bg-[#171717] text-[#C7FF3D]',
          border: 'border-[#D6D2C8]',
          text: 'text-[#1A5319]',
          gridCode: 'GRID 7F-A1 / SECURE',
        };
    }
  };

  const getZoneLetter = (idx: number) => {
    return ['ZONE A', 'ZONE B', 'ZONE C', 'ZONE D'][idx % 4];
  };

  return (
    <div className="bg-[#ECE9E0] border border-[#D6D2C8] rounded-sm p-3.5 shadow-none flex flex-col gap-3 font-sans">
      {/* Topology Header */}
      <div className="flex items-center justify-between border-b border-[#D6D2C8] pb-2">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 font-mono font-bold text-xs text-[#171717]">
            <Crosshair className="w-3.5 h-3.5 text-[#171717]" />
            <span>BORDER SECTOR TOPOLOGY // 4 TACTICAL QUADRANTS</span>
          </div>
          <span className="hidden sm:inline text-[10px] font-mono text-[#5E5E5E]">
            COORDINATES: LAT 31°18'N / LON 74°35'E
          </span>
        </div>

        <div className="flex items-center gap-2">
          {selectedSectorId && (
            <button
              onClick={() => onSelectSector(null)}
              className="text-[10px] font-mono text-[#171717] hover:underline px-2 py-0.5 rounded-sm bg-[#FFFFFF] border border-[#D6D2C8]"
            >
              [CLEAR FILTER]
            </button>
          )}
          <span className="text-[10px] font-mono font-semibold text-[#5E5E5E]">
            REAL-TIME TOPOLOGICAL SYNTHESIS
          </span>
        </div>
      </div>

      {/* 4-Sector Technical Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
        {sectors.map((sector, idx) => {
          const signal = getSectorSignal(sector.risk_level);
          const isSelected = selectedSectorId === sector.sector_id;
          const zoneTag = getZoneLetter(idx);

          return (
            <div
              key={sector.sector_id}
              onClick={() => onSelectSector(isSelected ? null : sector.sector_id)}
              className={`p-3 rounded-sm border transition-all cursor-pointer flex flex-col justify-between gap-2.5 bg-[#FFFFFF] ${
                isSelected
                  ? 'border-[#171717] ring-2 ring-[#171717]/80 bg-[#FFFFFF]'
                  : 'border-[#D6D2C8] hover:border-[#171717]/60'
              }`}
            >
              {/* Header: Zone & Grid Coordinate */}
              <div className="flex items-center justify-between border-b border-[#ECE9E0] pb-1.5">
                <div className="flex items-center gap-1.5">
                  <span className={`w-2 h-2 rounded-full ${signal.dot}`} />
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono font-bold text-xs text-[#171717]">
                        {zoneTag}
                      </span>
                      <span className="text-[10px] font-mono text-[#5E5E5E]">
                        ({sector.sector_id})
                      </span>
                    </div>
                    <span className="text-[9px] font-mono text-[#8A877E] block">
                      {signal.gridCode}
                    </span>
                  </div>
                </div>

                <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-sm ${signal.badge}`}>
                  {sector.risk_level}
                </span>
              </div>

              {/* Middle Row: Metrics */}
              <div className="grid grid-cols-2 gap-1.5 bg-[#F4F1E8] p-2 rounded-sm border border-[#D6D2C8] text-[10px] font-mono">
                <div>
                  <span className="text-[#5E5E5E] block text-[8px] uppercase tracking-wider">PEAK SCORE</span>
                  <span className={`font-bold text-xs ${signal.text}`}>
                    {sector.highest_score.toFixed(1)} <span className="text-[9px] text-[#8A877E]">/ 100</span>
                  </span>
                </div>
                <div>
                  <span className="text-[#5E5E5E] block text-[8px] uppercase tracking-wider">INCIDENTS</span>
                  <span className={`font-bold text-xs ${sector.active_incidents_count > 0 ? signal.text : 'text-[#171717]'}`}>
                    {sector.active_incidents_count} <span className="text-[9px] text-[#8A877E]">ACTIVE</span>
                  </span>
                </div>
              </div>

              {/* Camera Nodes */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-[9px] text-[#5E5E5E] font-mono">
                  <span>CAMERA NODES:</span>
                  <span>{sector.cameras.length} ONLINE</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {sector.cameras.map((c) => (
                    <button
                      key={c}
                      onClick={(e) => {
                        e.stopPropagation();
                        if (onFocusCamera) onFocusCamera(c);
                      }}
                      className="px-1.5 py-0.5 bg-[#FFFFFF] hover:bg-[#171717] hover:text-[#C7FF3D] text-[#171717] border border-[#D6D2C8] rounded-sm text-[10px] font-mono font-medium transition"
                      title={`Focus Camera ${c}`}
                    >
                      ● {c}
                    </button>
                  ))}
                </div>
              </div>

              {/* Sector description */}
              <p className="text-[9px] text-[#5E5E5E] font-mono truncate">
                {sector.summary}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
