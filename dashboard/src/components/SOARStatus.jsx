import React from 'react';
import { motion } from 'framer-motion';
import { Clock } from 'lucide-react';

const STATES = ['IDLE', 'SCANNING_DETECTED', 'THREAT_CONFIRMED', 'TRAP_DEPLOYING', 'TRAP_ACTIVE', 'PROFILING', 'REPORT_GENERATING', 'CONTAINED'];

export default function SOARStatus({ currentState = 'IDLE', timeline = [] }) {
  const idx = Math.max(0, STATES.indexOf(currentState));
  
  return (
    <div className="shadow-ot-card p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="text-xs text-on-surface-variant">SOAR Playbook</div>
        {timeline.length > 0 && (
          <div className="flex items-center gap-1 text-[10px] text-primary/70">
            <Clock size={10} />
            <span>Attack Lifecycle</span>
          </div>
        )}
      </div>
      
      {/* Progress bar */}
      <div className="flex items-center gap-1.5 pb-3 mb-3 border-b border-white/5">
        {STATES.map((state, i) => (
          <div key={state} className="flex items-center gap-1">
            <motion.div
              animate={{ scale: i === idx ? [1, 1.15, 1] : 1 }}
              transition={{ duration: 1.2, repeat: i === idx ? Infinity : 0 }}
              className={`w-2.5 h-2.5 rounded-full ${i <= idx ? 'bg-primary' : 'bg-slate-600'}`}
            />
            <span className={`text-[9px] ${i <= idx ? 'text-on-surface' : 'text-slate-500'}`}>{state}</span>
            {i < STATES.length - 1 && <div className={`w-3 h-[1px] ${i < idx ? 'bg-primary' : 'bg-slate-700'}`} />}
          </div>
        ))}
      </div>
      
      {/* Timeline with timestamps */}
      {timeline.length > 0 && (
        <div className="space-y-1.5 max-h-[180px] overflow-y-auto">
          {timeline.map((item, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              className="flex items-start gap-2 text-[10px]"
            >
              <span className="font-mono text-primary/90 min-w-[52px]">{item.time}</span>
              <div className="flex-1 flex items-center gap-1.5">
                <div className="w-1 h-1 rounded-full bg-primary/60" />
                <span className="text-slate-300">{item.event}</span>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
