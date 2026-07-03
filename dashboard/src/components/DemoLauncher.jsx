import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, RotateCcw, AlertTriangle, CheckCircle2, Circle, Loader2, Target, Shield, Cpu, Activity, FileText } from 'lucide-react';

const STAGES = [
  { 
    id: 'attack', 
    label: 'Infiltration', 
    desc: 'Attacker probing Modbus/TCP ports',
    icon: <Target size={14} />
  },
  { 
    id: 'detect', 
    label: 'Detection', 
    desc: 'LSTM AI flagging traffic anomalies',
    icon: <Activity size={14} />
  },
  { 
    id: 'trap', 
    label: 'Deception', 
    desc: 'Rerouting traffic to ephemeral honeypot',
    icon: <Shield size={14} />
  },
  { 
    id: 'profile', 
    label: 'Profiling', 
    desc: 'Extracting attacker behavioral DNA',
    icon: <Cpu size={14} />
  },
  { 
    id: 'report', 
    label: 'Reporting', 
    desc: 'Compiling SOAR incident forensics',
    icon: <FileText size={14} />
  },
];

const socketUrl = import.meta.env.DEV ? 'http://localhost:3000' : window.location.origin;

export default function DemoLauncher({ socket }) {
  const [mode, setMode] = useState('IDLE');
  const [sessionId, setSessionId] = useState(null);
  const [completedStages, setCompletedStages] = useState(new Set());
  const [error, setError] = useState(null);
  const [target, setTarget] = useState('10.5.0.10');

  const resetLocal = useCallback(() => {
    setMode('IDLE');
    setSessionId(null);
    setCompletedStages(new Set());
    setError(null);
  }, []);

  useEffect(() => {
    if (!socket) return;

    const onAlert = () => setCompletedStages(prev => new Set(prev).add('detect'));
    const onTrap = () => setCompletedStages(prev => new Set(prev).add('trap'));
    const onProfile = () => setCompletedStages(prev => new Set(prev).add('profile'));
    const onReport = () => setCompletedStages(prev => new Set(prev).add('report'));
    const onReset = () => resetLocal();
    const onPlaybook = (data) => {
      if (data.state === 'CONTAINED') setMode('CONTAINED');
    };

    socket.on('alert', onAlert);
    socket.on('trap_deployed', onTrap);
    socket.on('profile_final', onProfile);
    socket.on('report_ready', onReport);
    socket.on('system_reset', onReset);
    socket.on('playbook_update', onPlaybook);

    return () => {
      socket.off('alert', onAlert);
      socket.off('trap_deployed', onTrap);
      socket.off('profile_final', onProfile);
      socket.off('report_ready', onReport);
      socket.off('system_reset', onReset);
      socket.off('playbook_update', onPlaybook);
    };
  }, [socket, resetLocal]);

  const startDemo = async () => {
    setError(null);
    setCompletedStages(new Set(['attack']));
    setMode('RUNNING');
    try {
      const res = await fetch(`${socketUrl}/api/demo/start`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target })
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.status === 'busy' ? 'System busy — reset first' : data.message);
        setMode('IDLE');
        return;
      }
      setSessionId(data.session_id);
    } catch (e) {
      setError(e.message);
      setMode('IDLE');
    }
  };

  const resetDemo = async () => {
    setMode('RESETTING');
    try {
      await fetch(`${socketUrl}/api/demo/reset`, { method: 'POST' });
      resetLocal();
    } catch (e) {
      setError(e.message);
      setMode('IDLE');
    }
  };

  const isStageDone = (id) => completedStages.has(id);
  const currentStageIdx = STAGES.findIndex(s => !completedStages.has(s.id));

  return (
    <div className="fixed bottom-8 right-8 z-[100] w-[340px] pointer-events-none">
      <AnimatePresence mode="wait">
        {mode === 'IDLE' && (
          <motion.div
            key="idle"
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="shadow-ot-card pointer-events-auto p-6 bg-gradient-to-br from-[#1e293b] to-[#0f172a] border-primary/20"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 rounded-lg bg-primary/10 border border-primary/20">
                <Activity className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white tracking-wider uppercase">Mission Control</h4>
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Ready for Simulation</p>
              </div>
            </div>

            {error && (
              <div className="text-[10px] font-bold text-red-400 bg-red-400/5 border border-red-400/20 px-3 py-2 rounded-lg mb-4 flex items-center gap-2">
                <AlertTriangle size={12} />
                {error}
              </div>
            )}

            <div className="space-y-3">
              <button
                onClick={() => setMode('CONFIRMING')}
                className="w-full group flex items-center justify-between bg-primary hover:bg-cyan-400 text-[#0a0b10] px-4 py-3 rounded-xl font-bold text-xs transition-all shadow-lg shadow-primary/20"
              >
                <span className="tracking-widest uppercase">Start Simulation</span>
                <Play className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="currentColor" />
              </button>
              
              <button
                onClick={resetDemo}
                className="w-full flex items-center justify-center gap-2 bg-slate-800/50 hover:bg-slate-800 border border-white/5 text-slate-400 hover:text-white px-4 py-3 rounded-xl text-[10px] font-bold tracking-widest uppercase transition-all"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Reset Grid
              </button>
            </div>
          </motion.div>
        )}

        {mode === 'CONFIRMING' && (
          <motion.div
            key="confirm"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="shadow-ot-card pointer-events-auto p-6 border-red-500/30"
          >
            <div className="flex items-center gap-3 mb-6 text-red-400">
              <Target size={20} />
              <h4 className="text-sm font-bold tracking-widest uppercase">Select Vector</h4>
            </div>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">Target Controller</label>
                <div className="grid grid-cols-2 gap-2">
                  {['10.5.0.10', '10.5.0.11'].map(ip => (
                    <button
                      key={ip}
                      onClick={() => setTarget(ip)}
                      className={`px-3 py-4 rounded-xl border text-[10px] font-bold transition-all
                        ${target === ip 
                          ? 'bg-primary/10 border-primary text-primary' 
                          : 'bg-slate-800/50 border-white/5 text-slate-500 hover:border-white/10'}`}
                    >
                      {ip === '10.5.0.10' ? 'PLC-ALPHA' : 'PLC-BRAVO'}
                      <div className="opacity-50 font-mono mt-1">{ip}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => setMode('IDLE')}
                  className="flex-1 py-3 rounded-xl border border-white/5 text-slate-500 font-bold text-[10px] uppercase tracking-widest hover:bg-white/5 transition-all"
                >
                  Cancel
                </button>
                <button
                  onClick={startDemo}
                  className="flex-1 py-3 rounded-xl bg-red-500 hover:bg-red-400 text-[#0a0b10] font-bold text-[10px] uppercase tracking-widest shadow-lg shadow-red-500/20 transition-all"
                >
                  Execute
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {(mode === 'RUNNING' || mode === 'CONTAINED') && (
          <motion.div
            key="running"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="shadow-ot-card pointer-events-auto p-6 overflow-hidden"
          >
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3">
                {mode === 'CONTAINED' ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                ) : (
                  <Loader2 className="w-5 h-5 text-primary animate-spin" />
                )}
                <div>
                  <h4 className={`text-sm font-bold tracking-wider uppercase ${mode === 'CONTAINED' ? 'text-emerald-500' : 'text-white'}`}>
                    {mode === 'CONTAINED' ? 'Mission Success' : 'Live Simulation'}
                  </h4>
                  <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">
                    {mode === 'CONTAINED' ? 'Threat Fully Contained' : 'Active Engagement'}
                  </p>
                </div>
              </div>
            </div>

            <div className="relative space-y-6 before:content-[''] before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-[1px] before:bg-slate-800">
              {STAGES.map((stage, idx) => {
                const done = isStageDone(stage.id);
                const active = !done && idx === currentStageIdx && mode === 'RUNNING';
                
                return (
                  <div key={stage.id} className="relative flex items-start gap-4 pl-1">
                    <div className={`relative z-10 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all duration-500
                      ${done ? 'bg-emerald-500 border-emerald-400' : active ? 'bg-[#0a0b10] border-primary scale-125 shadow-[0_0_10px_var(--primary-glow)]' : 'bg-[#0a0b10] border-slate-800'}`}>
                      {done ? <CheckCircle2 size={10} className="text-[#0a0b10]" /> : active ? <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" /> : <div className="w-1 h-1 rounded-full bg-slate-800" />}
                    </div>
                    
                    <div className="flex-1 -mt-0.5">
                      <div className={`text-[11px] font-bold uppercase tracking-widest transition-colors duration-500
                        ${done ? 'text-emerald-500' : active ? 'text-primary' : 'text-slate-600'}`}>
                        {stage.label}
                      </div>
                      <div className={`text-[9px] transition-opacity duration-500 ${active ? 'opacity-100' : 'opacity-40'}`}>
                        {stage.desc}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <button
              onClick={resetDemo}
              className="mt-8 w-full flex items-center justify-center gap-2 bg-slate-800/50 hover:bg-slate-800 border border-white/5 text-slate-400 hover:text-white px-4 py-3 rounded-xl text-[10px] font-bold tracking-widest uppercase transition-all"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Terminate & Reset
            </button>
          </motion.div>
        )}

        {mode === 'RESETTING' && (
          <motion.div
            key="resetting"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="shadow-ot-card pointer-events-auto p-6 flex flex-col items-center justify-center gap-4"
          >
            <div className="relative">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
              <motion.div 
                animate={{ scale: [1, 1.5], opacity: [0.5, 0] }}
                transition={{ duration: 1, repeat: Infinity }}
                className="absolute inset-0 bg-primary rounded-full -z-10"
              />
            </div>
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Reinitializing Grid...</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
