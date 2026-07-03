import React, { useState, useEffect } from 'react';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Legend,
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
} from 'recharts';
import { Dna, AlertTriangle, Clock, Activity, CheckCircle } from 'lucide-react';

const FEATURE_LABELS = {
  command_rate:     'Command Rate',
  scan_coverage:    'Scan Coverage',
  automation_score: 'Automation',
  modbus_expertise: 'MB Expertise',
  write_aggression: 'Write Aggression',
  lateral_attempts: 'Lateral Movement',
  stealth_index:    'Stealth Index',
};

const APT_COLORS = {
  triton_trisis:         '#ef4444',
  industroyer:           '#f97316',
  pipedream:             '#a855f7',
  darkside_ics:          '#ec4899',
  sandworm:              '#3b82f6',
  generic_script_kiddie: '#22c55e',
};

const COMMAND_BADGE_COLORS = {
  read:      'bg-blue-500/20 text-blue-400 border border-blue-500/30',
  write:     'bg-red-500/20 text-red-400 border border-red-500/30',
  broadcast: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30',
  invalid:   'bg-gray-500/20 text-gray-400 border border-gray-500/30',
  deploy:    'bg-green-500/20 text-green-400 border border-green-500/30',
};

function getCommandType(event) {
  if (event.event === 'deployed') return 'deploy';
  const fc = event.function_code;
  if (!fc) return 'invalid';
  if ([5, 6, 15, 16, 22, 23].includes(fc)) return 'write';
  if ([1, 2, 3, 4].includes(fc)) return 'read';
  if (event.is_broadcast) return 'broadcast';
  return 'invalid';
}

function MatchBadge({ match, isTop }) {
  if (!match) return null;
  const pct    = Math.round(match.score * 100);
  const color  = APT_COLORS[match.apt] || '#94a3b8';
  const isLikely = match.likely_apt;

  return (
    <div
      className={`rounded-xl p-4 border ${isTop ? 'col-span-2' : ''}`}
      style={{ borderColor: color + '55', background: color + '11' }}
    >
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-4 min-w-0 flex-1">
          {isLikely && <AlertTriangle size={14} className="flex-shrink-0" style={{ color }} />}
          <span className="font-mono font-bold text-sm truncate" style={{ color }}>
            {match.label}
          </span>
        </div>
        <span
          className={`text-2xl font-black font-mono flex-shrink-0 ${isTop ? 'text-3xl' : ''}`}
          style={{ color }}
        >
          {pct}%
        </span>
      </div>
      {isTop && (
        <p className="text-xs text-slate-400 mt-1 leading-relaxed line-clamp-2">
          {match.description}
        </p>
      )}
      {isTop && (
        <p className="text-xs text-slate-500 mt-1">Source: {match.source}</p>
      )}
      {isLikely && isTop && (
        <div className="mt-2 px-2 py-1 rounded text-xs font-semibold inline-block"
          style={{ background: color + '22', color }}>
          ⚠ LIKELY APT — Confidence {pct}%
        </div>
      )}
    </div>
  );
}

export default function AttackerProfile({ profile, profileUpdating }) {
  const [activeTab, setActiveTab] = useState('radar');

  if (!profile) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-slate-500 gap-4">
        <Dna size={48} className="opacity-30" />
        <p className="text-sm">No active attacker profile. Deploy a trap to begin DNA analysis.</p>
      </div>
    );
  }

  const { features, apt_matches, trap_id, generated_at, status, timeline } = profile;
  const topMatch   = apt_matches?.[0];
  const topColor   = topMatch ? (APT_COLORS[topMatch.apt] || '#94a3b8') : '#94a3b8';

  // ── Radar data ─────────────────────────────────────────────────────────────
  const radarData = Object.keys(FEATURE_LABELS).map(key => ({
    subject:   FEATURE_LABELS[key],
    attacker:  Math.round((features?.[key] ?? 0) * 100),
    baseline:  topMatch ? Math.round((topMatch.baseline?.[key] ?? 0) * 100) : 0,
  }));

  // ── Bar chart data ─────────────────────────────────────────────────────────
  const barData = Object.keys(FEATURE_LABELS).map(key => ({
    name:  FEATURE_LABELS[key],
    value: Math.round((features?.[key] ?? 0) * 100),
  }));

  // ── Timeline data ──────────────────────────────────────────────────────────
  const timelineEvents = timeline ?? [
    { event: 'deployed',       timestamp: Date.now() / 1000 - 120, function_code: null },
    { event: 'modbus_command', timestamp: Date.now() / 1000 - 100, function_code: 3  },
    { event: 'modbus_command', timestamp: Date.now() / 1000 - 95,  function_code: 16 },
    { event: 'modbus_command', timestamp: Date.now() / 1000 - 90,  function_code: 16 },
    { event: 'modbus_command', timestamp: Date.now() / 1000 - 85,  function_code: 1  },
    { event: 'modbus_command', timestamp: Date.now() / 1000 - 60,  function_code: 16 },
    { event: 'modbus_command', timestamp: Date.now() / 1000 - 30,  function_code: 16 },
  ];

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Dna size={22} style={{ color: topColor }} />
          <div>
            <h2 className="font-bold text-lg text-white">Attacker DNA Profile</h2>
            <p className="text-xs text-slate-400 font-mono">Trap: {trap_id}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {profileUpdating ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-yellow-500/10 border border-yellow-500/30 text-yellow-400 text-xs animate-pulse">
              <Activity size={12} />
              Profile updating…
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/30 text-green-400 text-xs">
              <CheckCircle size={12} />
              Profile finalized
            </div>
          )}
          <span className="text-xs text-slate-500 font-mono">
            {generated_at ? new Date(generated_at).toLocaleTimeString() : ''}
          </span>
        </div>
      </div>

      {/* APT Match Cards */}
      <div className="grid grid-cols-3 gap-3">
        {apt_matches?.map((m, i) => (
          <MatchBadge key={m.apt} match={m} isTop={i === 0} />
        ))}
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-slate-700">
        {['radar', 'scores', 'timeline'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium capitalize transition-colors
              ${activeTab === tab
                ? 'border-b-2 text-white'
                : 'text-slate-400 hover:text-slate-300'}`}
            style={activeTab === tab ? { borderColor: topColor, color: topColor } : {}}
          >
            {tab === 'radar' ? 'Behavior Radar' : tab === 'scores' ? '7 Dimensions' : 'Command Timeline'}
          </button>
        ))}
      </div>

      {/* Radar chart */}
      {activeTab === 'radar' && (
        <div className="bg-slate-800/40 rounded-xl p-4 border border-slate-700/50">
          <ResponsiveContainer width="100%" height={340}>
            <RadarChart data={radarData} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
              <PolarGrid stroke="#334155" />
              <PolarAngleAxis
                dataKey="subject"
                tick={{ fill: '#94a3b8', fontSize: 11, fontFamily: 'monospace' }}
              />
              <PolarRadiusAxis
                angle={90}
                domain={[0, 100]}
                tick={{ fill: '#475569', fontSize: 9 }}
                axisLine={false}
              />
              <Radar
                name="Attacker"
                dataKey="attacker"
                stroke={topColor}
                fill={topColor}
                fillOpacity={0.25}
                strokeWidth={2}
              />
              <Radar
                name={topMatch?.label ?? 'APT Baseline'}
                dataKey="baseline"
                stroke="#94a3b8"
                fill="#94a3b8"
                fillOpacity={0.08}
                strokeWidth={1.5}
                strokeDasharray="4 3"
              />
              <Legend
                wrapperStyle={{ fontSize: '12px', color: '#94a3b8', paddingTop: '12px' }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Bar chart */}
      {activeTab === 'scores' && (
        <div className="bg-slate-800/40 rounded-xl p-4 border border-slate-700/50">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={barData}
              layout="vertical"
              margin={{ left: 110, right: 30, top: 5, bottom: 5 }}
            >
              <XAxis type="number" domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 10 }} />
              <YAxis
                type="category"
                dataKey="name"
                width={110}
                tick={{ fill: '#94a3b8', fontSize: 11, fontFamily: 'monospace' }}
              />
              <Tooltip
                formatter={(v) => [`${v}%`]}
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {barData.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={entry.value > 70 ? '#ef4444' : entry.value > 40 ? '#f97316' : '#3b82f6'}
                    opacity={0.85}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Timeline */}
      {activeTab === 'timeline' && (
        <div className="bg-slate-800/40 rounded-xl border border-slate-700/50 max-h-72 overflow-y-auto">
          {timelineEvents.map((ev, i) => {
            const type  = getCommandType(ev);
            const badge = COMMAND_BADGE_COLORS[type] || COMMAND_BADGE_COLORS.invalid;
            const ts    = ev.timestamp
              ? new Date(ev.timestamp * 1000).toLocaleTimeString()
              : '--:--:--';
            return (
              <div
                key={i}
                className="flex items-center gap-3 px-4 py-2.5 border-b border-slate-700/40 last:border-0 hover:bg-slate-700/20 transition-colors"
              >
                <Clock size={12} className="text-slate-500 flex-shrink-0" />
                <span className="text-xs font-mono text-slate-500 w-20 flex-shrink-0">{ts}</span>
                <span className={`text-xs px-2 py-0.5 rounded font-mono uppercase flex-shrink-0 ${badge}`}>
                  {type}
                </span>
                <span className="text-xs text-slate-400 font-mono truncate">
                  {ev.event === 'deployed'
                    ? 'Trap deployed — attacker redirected'
                    : `FC ${ev.function_code ?? '?'} → reg 0x${(ev.register ?? 0).toString(16).padStart(4, '0').toUpperCase()}`}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
