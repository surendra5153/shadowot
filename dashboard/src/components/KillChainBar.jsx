import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const TACTICS = [
  { 
    id: 'initial-access', 
    label: 'Initial Access',
    shortLabel: 'Initial',
    description: 'Attacker gains entry to the ICS network through exploitation or credential compromise.'
  },
  { 
    id: 'execution', 
    label: 'Execution',
    shortLabel: 'Exec',
    description: 'Malicious code or commands are executed on target systems.'
  },
  { 
    id: 'persistence', 
    label: 'Persistence',
    shortLabel: 'Persist',
    description: 'Attacker establishes foothold to maintain access across system restarts.'
  },
  { 
    id: 'privilege-escalation', 
    label: 'Privilege Escalation',
    shortLabel: 'Priv Esc',
    description: 'Attacker gains higher-level permissions on systems or networks.'
  },
  { 
    id: 'defense-evasion', 
    label: 'Defense Evasion',
    shortLabel: 'Evasion',
    description: 'Techniques used to avoid detection by security systems.'
  },
  { 
    id: 'lateral-movement', 
    label: 'Lateral Movement',
    shortLabel: 'Lateral',
    description: 'Attacker moves through the network to reach additional systems.'
  },
  { 
    id: 'collection', 
    label: 'Collection',
    shortLabel: 'Collect',
    description: 'Gathering information and data from target systems.'
  },
  { 
    id: 'command-and-control', 
    label: 'Command & Control',
    shortLabel: 'C2',
    description: 'Communication channel established between attacker and compromised systems.'
  },
  { 
    id: 'inhibit-response-function', 
    label: 'Inhibit Response',
    shortLabel: 'Inhibit',
    description: 'Preventing safety or protective functions from executing properly.'
  },
  { 
    id: 'impair-process-control', 
    label: 'Impair Control',
    shortLabel: 'Impair',
    description: 'Disrupting or manipulating industrial process control logic.'
  },
  { 
    id: 'impact', 
    label: 'Impact',
    shortLabel: 'Impact',
    description: 'Final objective achieved - disruption, damage, or manipulation of operations.'
  }
];

const KillChainBar = ({ currentStage, confirmedTechniques = [] }) => {
  const [hoveredIdx, setHoveredIdx] = useState(null);
  const currentIdx = TACTICS.findIndex(t => t.id === currentStage);
  const progress = ((currentIdx + 1) / TACTICS.length) * 100;

  // Get detection timestamp for current stage (simulated)
  const getTimestamp = (idx) => {
    if (idx > currentIdx) return null;
    const now = new Date();
    const offset = (currentIdx - idx) * 3; // 3 seconds apart
    const time = new Date(now.getTime() - offset * 1000);
    return time.toTimeString().split(' ')[0];
  };

  return (
    <div className="shadow-ot-card p-6 bg-gradient-to-r from-[#161a27] to-[#1a1e2e]">
      <div className="flex justify-between items-center mb-10">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          <h3 className="text-label-caps text-slate-300">ATT&CK for ICS Kill Chain</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-primary/70">THREAT_COVERAGE:</span>
          <span className="text-xs font-mono text-primary px-3 py-1 bg-primary/10 rounded-full border border-primary/20">
            {confirmedTechniques.length} Techniques Identified
          </span>
        </div>
      </div>

      {/* Desktop View: Horizontal */}
      <div className="hidden lg:block relative px-2 pb-16">
        {/* Background Track */}
        <div className="absolute top-[7px] left-0 w-full h-[2px] bg-slate-800 rounded-full" />
        
        {/* Active Progress Track */}
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 1.5, ease: "easeOut" }}
          className="absolute top-[7px] left-0 h-[2px] bg-gradient-to-r from-primary via-blue-500 to-red-500 rounded-full z-10 shadow-[0_0_10px_rgba(76,215,246,0.5)]"
        />

        <div className="relative flex justify-between">
          {TACTICS.map((tactic, idx) => {
            const isReached = idx <= currentIdx;
            const isCurrent = idx === currentIdx;
            const isHovered = hoveredIdx === idx;
            
            return (
              <div 
                key={tactic.id} 
                className="flex flex-col items-center relative"
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
              >
                {/* Node Marker */}
                <div className="relative z-20">
                  <motion.div 
                    initial={false}
                    animate={{ 
                      scale: isCurrent ? 1.4 : isHovered ? 1.2 : 1,
                      backgroundColor: isReached ? (isCurrent ? '#ef4444' : '#4cd7f6') : '#1e293b',
                      borderColor: isReached ? (isCurrent ? '#f87171' : '#67e8f9') : '#334155'
                    }}
                    className={`w-4 h-4 rounded-full border-2 cursor-help transition-shadow duration-500 ${isReached ? 'shadow-[0_0_15px_rgba(76,215,246,0.3)]' : ''}`}
                  />
                  {isCurrent && (
                    <motion.div 
                      animate={{ scale: [1, 2], opacity: [0.5, 0] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                      className="absolute inset-0 bg-red-500 rounded-full -z-10"
                    />
                  )}
                </div>
                
                {/* Label - Always visible, no overlap */}
                <div className={`
                  absolute top-8 left-1/2 -translate-x-1/2 text-center
                  text-[8px] font-bold uppercase tracking-wider transition-all duration-500
                  ${isReached ? (isCurrent ? 'text-red-400' : 'text-primary') : 'text-slate-600'}
                  ${isCurrent ? 'scale-110' : 'scale-100'}
                  max-w-[60px]
                `}>
                  {tactic.shortLabel}
                </div>

                {/* Tooltip on Hover */}
                <AnimatePresence>
                  {isHovered && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 10 }}
                      className="absolute top-14 left-1/2 -translate-x-1/2 z-50 pointer-events-none"
                    >
                      <div className="bg-slate-900/95 border border-primary/30 rounded-lg p-3 shadow-2xl backdrop-blur-sm min-w-[220px] max-w-[280px]">
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-xs font-bold text-primary uppercase tracking-wider">
                            {tactic.label}
                          </div>
                          {isReached && (
                            <div className="text-[9px] font-mono text-slate-400">
                              {getTimestamp(idx)}
                            </div>
                          )}
                        </div>
                        <div className="text-[10px] text-slate-300 leading-relaxed">
                          {tactic.description}
                        </div>
                        {isReached && (
                          <div className="mt-2 pt-2 border-t border-slate-700">
                            <div className="text-[9px] text-emerald-400 font-mono">
                              ✓ DETECTED
                            </div>
                          </div>
                        )}
                      </div>
                      {/* Arrow pointer */}
                      <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-slate-900 border-l border-t border-primary/30 rotate-45" />
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </div>
      </div>

      {/* Mobile/Tablet View: Vertical Grid */}
      <div className="lg:hidden grid grid-cols-2 gap-3">
        {TACTICS.map((tactic, idx) => {
          const isReached = idx <= currentIdx;
          const isCurrent = idx === currentIdx;
          
          return (
            <div 
              key={tactic.id}
              className={`
                flex items-center gap-2 p-2 rounded-lg border transition-all duration-500
                ${isReached 
                  ? (isCurrent ? 'bg-red-500/10 border-red-500/30' : 'bg-primary/5 border-primary/20')
                  : 'bg-slate-800/30 border-slate-700/30'}
              `}
            >
              <motion.div
                animate={{ scale: isCurrent ? [1, 1.2, 1] : 1 }}
                transition={{ duration: 1.2, repeat: isCurrent ? Infinity : 0 }}
                className={`
                  w-3 h-3 rounded-full flex-shrink-0
                  ${isReached ? (isCurrent ? 'bg-red-500' : 'bg-primary') : 'bg-slate-600'}
                `}
              />
              <div className="flex flex-col">
                <div className={`
                  text-[9px] font-bold uppercase tracking-wider
                  ${isReached ? (isCurrent ? 'text-red-400' : 'text-primary') : 'text-slate-500'}
                `}>
                  {tactic.shortLabel}
                </div>
                {isReached && getTimestamp(idx) && (
                  <div className="text-[8px] font-mono text-slate-500">
                    {getTimestamp(idx)}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default KillChainBar;
