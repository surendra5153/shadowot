import React, { useState, useEffect } from 'react';
import { Dna, RefreshCw } from 'lucide-react';
import AttackerProfile from '../components/AttackerProfile';

const API_BASE = import.meta.env.DEV ? 'http://localhost:3000' : window.location.origin;

// Client-side mock profile for demo/dev mode (used when backend lacks Phase 3 endpoints)
const CLIENT_MOCK_PROFILE = {
  trap_id: 'demo-trap-001',
  generated_at: new Date().toISOString(),
  is_mock: true,
  features: {
    command_rate:     0.82,
    scan_coverage:    0.58,
    automation_score: 0.91,
    modbus_expertise: 0.93,
    write_aggression: 0.72,
    lateral_attempts: 0.48,
    stealth_index:    0.22,
  },
  apt_matches: [
    {
      apt: 'triton_trisis', label: 'TRITON/TRISIS', score: 0.87, likely_apt: true,
      description: 'TRITON/TRISIS — Targeting Schneider Electric Triconex safety systems. Highly automated, expert-level Modbus knowledge.',
      source: 'CISA ICS-CERT Advisory ICSA-18-100-03; Dragos Year in Review 2018',
      baseline: { command_rate: 0.85, scan_coverage: 0.60, automation_score: 0.92, modbus_expertise: 0.95, write_aggression: 0.75, lateral_attempts: 0.50, stealth_index: 0.25 },
    },
    {
      apt: 'pipedream', label: 'PIPEDREAM', score: 0.71, likely_apt: false,
      description: 'PIPEDREAM/INCONTROLLER — Extremely high expertise, low noise signature.',
      source: 'CISA/NSA/FBI/DOE Joint Advisory AA22-103A',
      baseline: { command_rate: 0.20, scan_coverage: 0.75, automation_score: 0.80, modbus_expertise: 0.98, write_aggression: 0.40, lateral_attempts: 0.70, stealth_index: 0.90 },
    },
    {
      apt: 'industroyer', label: 'INDUSTROYER', score: 0.64, likely_apt: false,
      description: 'Industroyer/Crashoverride — Ukraine power grid attacks.',
      source: 'ESET Industroyer whitepaper',
      baseline: { command_rate: 0.55, scan_coverage: 0.90, automation_score: 0.70, modbus_expertise: 0.88, write_aggression: 0.60, lateral_attempts: 0.65, stealth_index: 0.45 },
    },
  ],
  status: 'final',
  timeline: [
    { event: 'deployed',       timestamp: Date.now() / 1000 - 180, function_code: null, register: 0 },
    { event: 'modbus_command', timestamp: Date.now() / 1000 - 160, function_code: 3,  register: 0x0100 },
    { event: 'modbus_command', timestamp: Date.now() / 1000 - 145, function_code: 16, register: 0x1000 },
    { event: 'modbus_command', timestamp: Date.now() / 1000 - 130, function_code: 16, register: 0x1001 },
    { event: 'modbus_command', timestamp: Date.now() / 1000 - 115, function_code: 16, register: 0x2500 },
    { event: 'modbus_command', timestamp: Date.now() / 1000 - 100, function_code: 1,  register: 0x0050 },
    { event: 'modbus_command', timestamp: Date.now() / 1000 - 85,  function_code: 16, register: 0xF000 },
    { event: 'modbus_command', timestamp: Date.now() / 1000 - 70,  function_code: 16, register: 0xF001 },
    { event: 'modbus_command', timestamp: Date.now() / 1000 - 55,  function_code: 16, register: 0xFF00 },
    { event: 'modbus_command', timestamp: Date.now() / 1000 - 40,  function_code: 16, register: 0xFF10 },
    { event: 'modbus_command', timestamp: Date.now() / 1000 - 25,  function_code: 3,  register: 0x0200 },
    { event: 'modbus_command', timestamp: Date.now() / 1000 - 10,  function_code: 16, register: 0xFFFE },
  ],
};

export default function ProfilerPage({ socket }) {
  const [profiles, setProfiles]           = useState([]);
  const [selectedId, setSelectedId]       = useState(null);
  const [activeProfile, setActiveProfile] = useState(null);
  const [profileUpdating, setProfileUpdating] = useState(false);
  const [loading, setLoading]             = useState(false);

  // Load stored profiles on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/profiles`)
      .then(r => r.json())
      .then(data => {
        setProfiles(data);
        if (data.length > 0) {
          const latest = data[data.length - 1];
          setSelectedId(latest.trap_id);
          setActiveProfile(latest);
          setProfileUpdating(latest.status === 'updating');
        }
      })
      .catch(() => {});
  }, []);

  // Socket events from server
  useEffect(() => {
    if (!socket) return;

    const onUpdate = (data) => {
      setProfiles(prev => {
        const idx = prev.findIndex(p => p.trap_id === data.trap_id);
        if (idx >= 0) {
          const next = [...prev];
          next[idx]  = data;
          return next;
        }
        return [...prev, data];
      });
      if (data.trap_id === selectedId || !selectedId) {
        setActiveProfile(data);
        setSelectedId(data.trap_id);
        setProfileUpdating(data.status === 'updating');
      }
    };

    const onFinal = (data) => {
      onUpdate({ ...data, status: 'final' });
      setProfileUpdating(false);
    };

    socket.on('profile_update', onUpdate);
    socket.on('profile_final',  onFinal);

    return () => {
      socket.off('profile_update', onUpdate);
      socket.off('profile_final',  onFinal);
    };
  }, [socket, selectedId]);

  const loadProfile = async (trapId) => {
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/api/profile/${trapId}`);
      if (!resp.ok) throw new Error('Failed to fetch');
      const data = await resp.json();
      setActiveProfile(data);
      setSelectedId(trapId);
      setProfileUpdating(data.status === 'updating');
    } catch (e) {
      console.error('API failed, using client mock:', e);
      const data = { ...CLIENT_MOCK_PROFILE, trap_id: trapId };
      setActiveProfile(data);
      setSelectedId(trapId);
      setProfileUpdating(false);
    } finally {
      setLoading(false);
    }
  };

  const loadMockProfile = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/api/profile/mock-trap`, { method: 'POST' });
      if (!resp.ok) throw new Error('Failed to fetch');
      const data = await resp.json();
      setActiveProfile(data);
      setSelectedId(data.trap_id);
      setProfileUpdating(false);
      setProfiles(prev => {
        const idx = prev.findIndex(p => p.trap_id === data.trap_id);
        if (idx >= 0) { const n=[...prev]; n[idx]=data; return n; }
        return [...prev, data];
      });
    } catch (e) {
      console.error('API failed, using client mock:', e);
      const data = { ...CLIENT_MOCK_PROFILE };
      setActiveProfile(data);
      setSelectedId(data.trap_id);
      setProfileUpdating(false);
      setProfiles(prev => {
        const idx = prev.findIndex(p => p.trap_id === data.trap_id);
        if (idx >= 0) { const n=[...prev]; n[idx]=data; return n; }
        return [...prev, data];
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
      {/* Top bar */}
      <div className="h-14 border-b border-[#334155] flex items-center justify-between px-6 bg-[#141720] flex-shrink-0">
        <div className="flex items-center gap-3">
          <Dna size={18} className="text-purple-400" />
          <h1 className="font-sans font-semibold text-lg tracking-tight">Attacker DNA Profiler</h1>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadMockProfile}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/30
                       text-purple-400 text-xs font-medium hover:bg-purple-500/20 transition-colors disabled:opacity-50"
          >
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
            Load Demo Profile
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar: trap list */}
        <div className="w-56 border-r border-[#334155] bg-[#1A1E2E] overflow-y-auto flex-shrink-0">
          <div className="px-3 py-3">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Trap Sessions</p>
            {profiles.length === 0 ? (
              <p className="text-xs text-slate-600 italic">No sessions yet</p>
            ) : (
              profiles.map(p => (
                <button
                  key={p.trap_id}
                  onClick={() => loadProfile(p.trap_id)}
                  className={`w-full text-left px-3 py-2 rounded-lg mb-1 transition-colors text-xs font-mono
                    ${selectedId === p.trap_id
                      ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                      : 'text-slate-400 hover:bg-slate-700/40'}`}
                >
                  <div className="truncate">{p.trap_id}</div>
                  <div className="text-slate-600 text-[10px]">
                    {p.apt_matches?.[0]?.label ?? 'Unknown'}
                    {' · '}{Math.round((p.apt_matches?.[0]?.score ?? 0) * 100)}%
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Main content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-5xl mx-auto">
            {loading ? (
              <div className="flex items-center justify-center h-64 text-slate-500">
                <RefreshCw size={24} className="animate-spin mr-3" />
                Loading profile…
              </div>
            ) : (
              <AttackerProfile
                profile={activeProfile}
                profileUpdating={profileUpdating}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
