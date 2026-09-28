import React, { useState } from 'react';
import { ShieldAlert, CheckCircle2, Search, ArrowRight, Eye, UserCheck, FileText } from 'lucide-react';
import { Incident, UserRole } from '../types';

interface IncidentCommandPanelProps {
  incidents: Incident[];
  selectedSectorId: string | null;
  currentRole: UserRole;
  onOpenInvestigation: (incidentId: string) => void;
  onQuickAcknowledge: (incidentId: string) => void;
  onQuickInvestigate: (incidentId: string) => void;
  onQuickClose: (incidentId: string) => void;
}

export const IncidentCommandPanel: React.FC<IncidentCommandPanelProps> = ({
  incidents,
  selectedSectorId,
  currentRole,
  onOpenInvestigation,
  onQuickAcknowledge,
  onQuickInvestigate,
  onQuickClose,
}) => {
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const filteredIncidents = incidents.filter((inc) => {
    if (filterStatus !== 'ALL') {
      if (filterStatus === 'ACTIVE' && inc.status === 'CLOSED') return false;
      if (filterStatus !== 'ACTIVE' && inc.status !== filterStatus) return false;
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchesId = inc.incident_id.toLowerCase().includes(q);
      const matchesSubj = inc.subject_id.toLowerCase().includes(q);
      const matchesTitle = inc.title.toLowerCase().includes(q);
      if (!matchesId && !matchesSubj && !matchesTitle) return false;
    }
    return true;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'DETECTED':
      case 'VERIFIED':
      case 'CORRELATED':
      case 'ASSESSED':
        return 'bg-[#FF4D4D] text-[#FFFFFF] font-bold';
      case 'ACKNOWLEDGED':
        return 'bg-[#F5A623] text-[#171717] font-bold';
      case 'INVESTIGATING':
        return 'bg-[#171717] text-[#C7FF3D] font-bold';
      case 'CLOSED':
        return 'bg-[#ECE9E0] text-[#5E5E5E] border border-[#D6D2C8]';
      default:
        return 'bg-[#ECE9E0] text-[#171717] border border-[#D6D2C8]';
    }
  };

  return (
    <div className="bg-[#ECE9E0] border border-[#D6D2C8] rounded-sm p-3.5 shadow-none flex flex-col gap-3 font-sans">
      {/* Masthead */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#D6D2C8] pb-2.5">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 font-mono font-bold text-xs text-[#171717]">
            <ShieldAlert className="w-3.5 h-3.5 text-[#171717]" />
            <span>INCIDENT COMMAND & OPERATIONAL QUEUE ({filteredIncidents.length} / {incidents.length})</span>
          </div>
          <span className="hidden sm:inline text-[10px] font-mono text-[#5E5E5E]">
            HUMAN-IN-THE-LOOP FORENSIC DECISION CENTER
          </span>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center gap-2 flex-wrap font-mono text-xs">
          {/* Status Tabs */}
          <div className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm p-0.5 flex items-center">
            {['ALL', 'ACTIVE', 'ACKNOWLEDGED', 'INVESTIGATING', 'CLOSED'].map((st) => (
              <button
                key={st}
                onClick={() => setFilterStatus(st)}
                className={`px-2 py-0.5 rounded-sm transition text-[10px] font-semibold ${
                  filterStatus === st
                    ? 'bg-[#171717] text-[#F4F1E8]'
                    : 'text-[#5E5E5E] hover:text-[#171717]'
                }`}
              >
                {st}
              </button>
            ))}
          </div>

          {/* Search box */}
          <div className="relative">
            <input
              type="text"
              placeholder="SEARCH ID / SUBJ..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm pl-6 pr-2 py-0.5 text-[11px] font-mono text-[#171717] placeholder-[#8A877E] focus:outline-none focus:border-[#171717] w-32 sm:w-40"
            />
            <Search className="w-3 h-3 text-[#8A877E] absolute left-1.5 top-1.5" />
          </div>
        </div>
      </div>

      {/* Incident List */}
      <div className="overflow-x-auto bg-[#FFFFFF] border border-[#D6D2C8] rounded-sm">
        {filteredIncidents.length === 0 ? (
          <div className="p-8 text-center text-[#5E5E5E] font-mono text-xs flex flex-col items-center justify-center gap-1.5">
            <ShieldAlert className="w-6 h-6 text-[#8A877E]" />
            <span className="font-semibold text-[#171717]">NO ACTIVE INCIDENTS MATCHING FILTERS</span>
            <span className="text-[10px] text-[#8A877E]">Trigger a test scenario in Simulation Controls to generate incidents.</span>
          </div>
        ) : (
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="bg-[#ECE9E0] border-b border-[#D6D2C8] text-[#5E5E5E] uppercase text-[9px] font-bold">
                <th className="py-2 px-3">INCIDENT ID / SUBJECT</th>
                <th className="py-2 px-3">FORENSIC TITLE & SUMMARY</th>
                <th className="py-2 px-3">CAMERA NODES</th>
                <th className="py-2 px-3">STATUS</th>
                <th className="py-2 px-3">TIMESTAMP</th>
                <th className="py-2 px-3 text-right">OPERATOR ACTIONS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#ECE9E0]">
              {filteredIncidents.map((inc) => (
                <tr
                  key={inc.incident_id}
                  className="hover:bg-[#F4F1E8] transition group cursor-pointer"
                  onClick={() => onOpenInvestigation(inc.incident_id)}
                >
                  {/* ID & Subject */}
                  <td className="py-2.5 px-3">
                    <div className="flex flex-col">
                      <span className="font-bold text-[#171717] group-hover:underline">
                        {inc.incident_id}
                      </span>
                      <span className="text-[10px] text-[#5E5E5E]">
                        SUBJ: {inc.subject_id}
                      </span>
                    </div>
                  </td>

                  {/* Title & Summary */}
                  <td className="py-2.5 px-3 max-w-xs">
                    <div className="flex flex-col">
                      <span className="font-bold text-[#171717] truncate">
                        {inc.title}
                      </span>
                      <span className="text-[10px] text-[#5E5E5E] line-clamp-1">
                        {inc.summary}
                      </span>
                    </div>
                  </td>

                  {/* Cameras Involved */}
                  <td className="py-2.5 px-3">
                    <div className="flex items-center gap-1 flex-wrap">
                      {inc.cameras_involved?.map((c) => (
                        <span
                          key={c}
                          className="px-1.5 py-0.2 rounded-sm bg-[#ECE9E0] border border-[#D6D2C8] text-[#171717] text-[10px] font-semibold"
                        >
                          {c}
                        </span>
                      ))}
                    </div>
                  </td>

                  {/* Lifecycle Status Badge */}
                  <td className="py-2.5 px-3">
                    <span className={`px-2 py-0.5 rounded-sm text-[9px] ${getStatusBadge(inc.status)}`}>
                      {inc.status}
                    </span>
                  </td>

                  {/* Timestamp */}
                  <td className="py-2.5 px-3 text-[#5E5E5E] text-[10px]">
                    {new Date(inc.created_at).toLocaleTimeString()}
                  </td>

                  {/* Operator Actions */}
                  <td className="py-2.5 px-3 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-1 font-mono text-[10px]">
                      {inc.status !== 'CLOSED' && inc.status !== 'ACKNOWLEDGED' && inc.status !== 'INVESTIGATING' && (
                        <button
                          onClick={() => onQuickAcknowledge(inc.incident_id)}
                          className="px-2 py-0.5 rounded-sm bg-[#FFFFFF] hover:bg-[#171717] hover:text-[#C7FF3D] text-[#171717] border border-[#D6D2C8] font-bold transition flex items-center gap-1"
                          title="Acknowledge Incident"
                        >
                          <UserCheck className="w-3 h-3" />
                          <span>ACK</span>
                        </button>
                      )}

                      {inc.status !== 'INVESTIGATING' && inc.status !== 'CLOSED' && (
                        <button
                          onClick={() => onQuickInvestigate(inc.incident_id)}
                          className="px-2 py-0.5 rounded-sm bg-[#FFFFFF] hover:bg-[#171717] hover:text-[#C7FF3D] text-[#171717] border border-[#D6D2C8] font-bold transition flex items-center gap-1"
                          title="Investigate"
                        >
                          <Eye className="w-3 h-3" />
                          <span>INVESTIGATE</span>
                        </button>
                      )}

                      {inc.status !== 'CLOSED' && (
                        <button
                          onClick={() => onQuickClose(inc.incident_id)}
                          className="px-2 py-0.5 rounded-sm bg-[#FFFFFF] hover:bg-[#171717] hover:text-[#C7FF3D] text-[#5E5E5E] border border-[#D6D2C8] font-bold transition flex items-center gap-1"
                          title="Close Incident"
                        >
                          <CheckCircle2 className="w-3 h-3 text-[#1A5319]" />
                          <span>CLOSE</span>
                        </button>
                      )}

                      <button
                        onClick={() => onOpenInvestigation(inc.incident_id)}
                        className="px-2.5 py-0.5 rounded-sm bg-[#171717] hover:bg-[#292929] text-[#F4F1E8] font-bold transition flex items-center gap-1"
                        title="Open Investigation Cockpit"
                      >
                        <FileText className="w-3 h-3 text-[#C7FF3D]" />
                        <span>COCKPIT</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
