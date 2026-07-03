import React, { useRef, useEffect } from 'react';
import { Terminal } from 'lucide-react';

export default function EventLog({ events }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  return (
    <div className="shadow-ot-card h-[400px] w-full flex flex-col relative">
      <div className="h-10 border-b border-white/5 flex items-center px-4 bg-white/5">
        <Terminal size={14} className="text-primary mr-2" />
        <span className="text-label-caps text-slate-300">Live Mission Logs</span>
      </div>
      
      <div 
        ref={scrollRef} 
        className="overflow-y-auto flex-1 font-mono p-4 space-y-2 scroll-smooth"
      >
        {events.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-slate-600 space-y-2">
            <div className="w-8 h-8 rounded-full border border-slate-800 flex items-center justify-center animate-pulse">
              <div className="w-2 h-2 rounded-full bg-slate-800" />
            </div>
            <span className="text-[10px] uppercase tracking-widest font-bold">Awaiting Telemetry...</span>
          </div>
        )}
        
        {events.map((evt, i) => {
          const isCritical = evt.status !== 'rerouted' && (evt.trigger || evt.anomaly_score > 0.5);
          const timestamp = new Date(evt.timestamp).toLocaleTimeString([], { hour12: false });
          
          return (
            <div 
              key={i} 
              className={`group flex items-start py-2 px-3 text-[11px] rounded-lg border transition-all duration-300
                ${isCritical 
                  ? 'bg-red-500/5 border-red-500/20 hover:border-red-500/40' 
                  : 'bg-slate-800/20 border-white/5 hover:border-white/10'}`}
            >
              <span className="text-slate-500 w-20 flex-shrink-0 font-bold tracking-tight">
                [{timestamp}]
              </span>
              
              <div className="flex flex-col flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`font-bold uppercase tracking-wider
                    ${isCritical ? 'text-red-400' : 'text-primary'}`}>
                    {evt.trigger || evt.status || 'EVENT_SIGNAL'}
                  </span>
                  {evt.anomaly_score && (
                    <span className="text-[9px] px-1.5 py-0.5 bg-red-500/10 text-red-500 rounded border border-red-500/20">
                      SCORE: {evt.anomaly_score.toFixed(3)}
                    </span>
                  )}
                </div>
                
                <div className="text-slate-400 truncate group-hover:text-slate-200 transition-colors">
                  {evt.attacker_ip && <span className="text-slate-600 mr-2">SRC:</span>}
                  {evt.attacker_ip && <span className="text-white/80">{evt.attacker_ip}</span>}
                  
                  {evt.target_plc && <span className="text-slate-600 mx-2">→</span>}
                  {evt.target_plc && <span className="text-primary/80">{evt.target_plc}</span>}
                  
                  {evt.trap_id && <span className="text-slate-600 mx-2">→</span>}
                  {evt.trap_id && <span className="text-cyan-400 font-bold">{evt.trap_id}</span>}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      
      <div className="h-6 bg-white/5 border-t border-white/5 flex items-center px-4">
        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse mr-2" />
        <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Socket Stream: Active</span>
      </div>
    </div>
  );
}
