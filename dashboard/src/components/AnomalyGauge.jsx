import React from 'react';
import { motion } from 'framer-motion';

export default function AnomalyGauge({ score }) {
  const percentage = Math.min(Math.max(score * 100, 0), 100);
  const isAlert = score > 0.7;
  const segments = Array.from({ length: 20 });
  
  return (
    <div className="shadow-ot-card p-6 flex flex-col justify-between h-32 relative overflow-hidden bg-gradient-to-br from-[#161a27] to-transparent">
      <div className="flex justify-between items-center mb-2">
        <span className="text-label-caps text-slate-400">Threat Detection Engine</span>
        <span className={`font-mono text-lg font-bold tracking-tighter transition-colors duration-500
          ${isAlert ? 'text-red-500 shadow-[0_0_10px_rgba(239,68,68,0.2)]' : 'text-primary'}`}>
          {score.toFixed(3)}
        </span>
      </div>

      <div className="flex flex-col gap-2">
        <div className="flex justify-between items-center px-1">
          <span className="text-[9px] font-bold text-slate-600 uppercase">Baseline</span>
          <span className="text-[9px] font-bold text-red-500/50 uppercase">Critical Threshold</span>
        </div>

        <div className="flex items-center gap-[2px] h-3">
          {segments.map((_, i) => {
            const segmentValue = (i / segments.length);
            const isActive = score > segmentValue;
            const isThreshold = i === 14; // 70%
            
            return (
              <motion.div
                key={i}
                initial={false}
                animate={{
                  backgroundColor: isActive 
                    ? (segmentValue > 0.7 ? '#ef4444' : '#4cd7f6') 
                    : '#1e293b',
                  boxShadow: isActive 
                    ? `0 0 10px ${segmentValue > 0.7 ? 'rgba(239,68,68,0.3)' : 'rgba(76,215,246,0.3)'}` 
                    : 'none'
                }}
                className={`flex-1 h-full rounded-[1px] transition-all duration-300 ${isThreshold ? 'border-r border-white/20' : ''}`}
              />
            );
          })}
        </div>
      </div>
      
      <div className="absolute top-0 right-0 p-2 opacity-5">
        <div className="w-16 h-16 border-t-2 border-r-2 border-primary rounded-tr-lg" />
      </div>
    </div>
  );
}
