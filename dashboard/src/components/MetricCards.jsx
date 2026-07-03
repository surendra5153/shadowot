import React from 'react';
import { Activity, ShieldAlert, Target, Clock, Zap, AlertTriangle } from 'lucide-react';

export default function MetricCards({ nodesOnline, threats, traps, uptime, riskScore = 0, riskLevel = "Low" }) {
  // Color mapping for risk levels
  const riskColors = {
    "Low": { text: "text-emerald-400", glow: "shadow-emerald-500/20", bg: "from-emerald-500/5 to-transparent", border: "border-emerald-500/20" },
    "Medium": { text: "text-yellow-400", glow: "shadow-yellow-500/20", bg: "from-yellow-500/5 to-transparent", border: "border-yellow-500/20" },
    "High": { text: "text-orange-400", glow: "shadow-orange-500/20", bg: "from-orange-500/5 to-transparent", border: "border-orange-500/20" },
    "Critical": { text: "text-red-400", glow: "shadow-red-500/20", bg: "from-red-500/5 to-transparent", border: "border-red-500/20" }
  };
  
  const riskStyle = riskColors[riskLevel] || riskColors["Low"];
  
  const cards = [
    { 
      title: "Active Nodes", 
      value: nodesOnline, 
      icon: <Activity />, 
      color: "text-blue-400",
      glow: "shadow-blue-500/20",
      bg: "from-blue-500/5 to-transparent"
    },
    { 
      title: "Threats Detected", 
      value: threats, 
      icon: <ShieldAlert />, 
      color: "text-red-400",
      glow: "shadow-red-500/20",
      bg: "from-red-500/5 to-transparent"
    },
    { 
      title: "Traps Active", 
      value: traps, 
      icon: <Target />, 
      color: "text-cyan-400",
      glow: "shadow-cyan-500/20",
      bg: "from-cyan-500/5 to-transparent"
    },
    { 
      title: "Risk Score", 
      value: riskScore,
      subtitle: riskLevel,
      icon: <AlertTriangle />, 
      color: riskStyle.text,
      glow: riskStyle.glow,
      bg: riskStyle.bg,
      border: riskStyle.border
    },
    { 
      title: "System Uptime", 
      value: `${uptime}s`, 
      icon: <Clock />, 
      color: "text-slate-400",
      glow: "shadow-slate-500/20",
      bg: "from-slate-500/5 to-transparent"
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
      {cards.map((card, i) => (
        <div key={i} className={`shadow-ot-card group p-6 flex flex-col justify-between h-32 bg-gradient-to-br ${card.bg} ${card.border ? `border ${card.border}` : ''}`}>
          <div className="flex justify-between items-start">
            <span className="text-[10px] font-bold tracking-[0.2em] uppercase text-slate-500 group-hover:text-slate-300 transition-colors">
              {card.title}
            </span>
            <div className={`p-2 rounded-lg bg-slate-800/50 ${card.color} group-hover:scale-110 transition-transform duration-300`}>
              {React.cloneElement(card.icon, { size: 18 })}
            </div>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-bold text-white tracking-tight">
              {card.value}
            </span>
            {card.subtitle && (
              <span className={`text-[11px] font-bold uppercase tracking-wider ${card.color}`}>{card.subtitle}</span>
            )}
            {i === 1 && threats > 0 && (
              <span className="text-[10px] text-red-500 font-mono animate-pulse">ACTIVE</span>
            )}
          </div>
          {/* Subtle bottom accent line */}
          <div className={`absolute bottom-0 left-0 h-[2px] bg-current transition-all duration-500 w-0 group-hover:w-full ${card.color} opacity-30`} />
        </div>
      ))}
    </div>
  );
}
