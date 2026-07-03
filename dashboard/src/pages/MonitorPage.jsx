import React, { useState, useEffect, useRef } from 'react';
import { Activity, Radio, Package, AlertTriangle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import AnomalyGauge from '../components/AnomalyGauge';
import TrafficSparkline from '../components/TrafficSparkline';

// Packet Stream Widget
function PacketStream({ events }) {
  const scrollRef = useRef(null);
  
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  // Filter for actual packet/modbus events
  const packetEvents = events.filter(e => 
    e.function_code || e.address || e.trigger
  ).slice(-20);

  // Map function codes to names
  const getFunctionName = (fc) => {
    const codes = {
      1: 'Read Coils',
      2: 'Read Discrete Inputs',
      3: 'Read Holding Registers',
      4: 'Read Input Registers',
      5: 'Write Single Coil',
      6: 'Write Single Register',
      15: 'Write Multiple Coils',
      16: 'Write Multiple Registers',
      23: 'Read/Write Multiple Registers'
    };
    return codes[fc] || `Function ${fc}`;
  };

  // Map register addresses to names
  const getRegisterName = (addr) => {
    if (addr >= 1000 && addr <= 1100) return 'Pressure';
    if (addr >= 2000 && addr <= 2100) return 'Temperature';
    if (addr >= 3000 && addr <= 3100) return 'Flow Rate';
    if (addr >= 4000 && addr <= 4100) return 'Valve Control';
    return `Register ${addr}`;
  };

  return (
    <div className="shadow-ot-card h-[500px] flex flex-col">
      <div className="h-12 border-b border-white/5 flex items-center justify-between px-4 bg-white/5">
        <div className="flex items-center gap-2">
          <Package size={14} className="text-primary" />
          <span className="text-label-caps text-slate-300">Live Packet Stream</span>
        </div>
        <div className="text-[9px] font-mono text-slate-500">
          {packetEvents.length} packets
        </div>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-2 scroll-smooth">
        {packetEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-600 space-y-2">
            <Radio className="w-8 h-8 opacity-30 animate-pulse" />
            <span className="text-[10px] uppercase tracking-widest font-bold">
              Awaiting Traffic...
            </span>
          </div>
        ) : (
          packetEvents.map((pkt, i) => {
            const isWrite = pkt.function_code >= 5;
            const isAnomaly = pkt.anomaly_score > 0.5;
            const timestamp = new Date(pkt.timestamp).toLocaleTimeString([], { 
              hour12: false, 
              hour: '2-digit', 
              minute: '2-digit', 
              second: '2-digit' 
            });

            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3 }}
                className={`p-3 rounded-lg border transition-all ${
                  isAnomaly
                    ? 'bg-red-500/10 border-red-500/30'
                    : isWrite
                    ? 'bg-yellow-500/5 border-yellow-500/20'
                    : 'bg-slate-800/30 border-slate-700/30'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <span className="text-[9px] font-mono text-slate-500">{timestamp}</span>
                  {isAnomaly && (
                    <span className="text-[8px] px-1.5 py-0.5 bg-red-500/20 text-red-400 rounded border border-red-500/30 font-bold">
                      ANOMALY
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-2 text-[10px]">
                  <div>
                    <span className="text-slate-600 font-bold">Src:</span>
                    <span className="ml-1 text-slate-300 font-mono">
                      {pkt.attacker_ip || 'unknown'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-600 font-bold">Dst:</span>
                    <span className="ml-1 text-primary font-mono">
                      {pkt.target_plc || pkt.dst_ip || 'unknown'}
                    </span>
                  </div>
                  <div className="col-span-2">
                    <span className="text-slate-600 font-bold">Protocol:</span>
                    <span className="ml-1 text-slate-300">Modbus TCP</span>
                  </div>
                  {pkt.function_code && (
                    <div className="col-span-2">
                      <span className="text-slate-600 font-bold">Function:</span>
                      <span className={`ml-1 font-mono ${isWrite ? 'text-yellow-400' : 'text-slate-300'}`}>
                        {getFunctionName(pkt.function_code)}
                      </span>
                    </div>
                  )}
                  {pkt.address && (
                    <div className="col-span-2">
                      <span className="text-slate-600 font-bold">Register:</span>
                      <span className="ml-1 text-cyan-400 font-mono">
                        {getRegisterName(pkt.address)}
                      </span>
                    </div>
                  )}
                  {pkt.anomaly_score && (
                    <div className="col-span-2">
                      <span className="text-slate-600 font-bold">Score:</span>
                      <span className="ml-1 text-red-400 font-mono">
                        {pkt.anomaly_score.toFixed(3)}
                      </span>
                    </div>
                  )}
                </div>
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
}

// Live Event Stream with synthesized lifecycle events
function LiveEventStream({ events, playbookState, alertActive, trapActive }) {
  const scrollRef = useRef(null);
  const [synthesizedEvents, setSynthesizedEvents] = useState([]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [synthesizedEvents]);

  // Generate synthesized lifecycle events based on state changes
  useEffect(() => {
    const timestamp = new Date().toLocaleTimeString([], { hour12: false });
    
    if (playbookState === 'DEMO_LAUNCHING') {
      setSynthesizedEvents(prev => [...prev, {
        timestamp,
        type: 'lifecycle',
        level: 'info',
        message: 'Attack simulation started'
      }]);
    } else if (playbookState === 'SCANNING_DETECTED') {
      setSynthesizedEvents(prev => [...prev, {
        timestamp,
        type: 'lifecycle',
        level: 'warning',
        message: 'Network scanning activity detected'
      }]);
    } else if (playbookState === 'THREAT_CONFIRMED' && alertActive) {
      setSynthesizedEvents(prev => [...prev, {
        timestamp,
        type: 'lifecycle',
        level: 'critical',
        message: 'Unauthorized Modbus write detected'
      }]);
    } else if (playbookState === 'TRAP_DEPLOYING') {
      setSynthesizedEvents(prev => [...prev, {
        timestamp,
        type: 'lifecycle',
        level: 'warning',
        message: 'PLC register modification attempt'
      }]);
    } else if (playbookState === 'TRAP_ACTIVE' && trapActive) {
      setSynthesizedEvents(prev => [...prev, {
        timestamp,
        type: 'lifecycle',
        level: 'warning',
        message: 'Anomaly threshold exceeded'
      }, {
        timestamp,
        type: 'lifecycle',
        level: 'success',
        message: 'Deception trap deployed'
      }, {
        timestamp,
        type: 'lifecycle',
        level: 'success',
        message: 'Malicious traffic redirected to honeypot'
      }]);
    } else if (playbookState === 'PROFILING') {
      setSynthesizedEvents(prev => [...prev, {
        timestamp,
        type: 'lifecycle',
        level: 'info',
        message: 'Behavioral profiling in progress'
      }]);
    } else if (playbookState === 'CONTAINED') {
      setSynthesizedEvents(prev => [...prev, {
        timestamp,
        type: 'lifecycle',
        level: 'success',
        message: 'Threat contained - report generated'
      }]);
    } else if (playbookState === 'IDLE' && synthesizedEvents.length > 0) {
      // Reset on system reset
      setSynthesizedEvents([]);
    }
  }, [playbookState, alertActive, trapActive]);

  // Merge synthesized events with real events
  const allEvents = [
    ...synthesizedEvents,
    ...events.map(e => ({
      timestamp: new Date(e.timestamp).toLocaleTimeString([], { hour12: false }),
      type: e.trigger ? 'alert' : 'event',
      level: e.anomaly_score > 0.5 ? 'critical' : e.status === 'rerouted' ? 'success' : 'info',
      message: e.trigger || e.status || 'Event',
      details: e
    }))
  ].slice(-50);

  const getLevelColor = (level) => {
    switch (level) {
      case 'critical': return { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400' };
      case 'warning': return { bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', text: 'text-yellow-400' };
      case 'success': return { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-400' };
      default: return { bg: 'bg-slate-800/30', border: 'border-slate-700/30', text: 'text-slate-300' };
    }
  };

  const getLevelIcon = (level) => {
    switch (level) {
      case 'critical': return '🔴';
      case 'warning': return '⚠️';
      case 'success': return '✓';
      default: return '•';
    }
  };

  return (
    <div className="shadow-ot-card h-[500px] flex flex-col">
      <div className="h-12 border-b border-white/5 flex items-center justify-between px-4 bg-white/5">
        <div className="flex items-center gap-2">
          <Activity size={14} className="text-primary" />
          <span className="text-label-caps text-slate-300">Live Event Stream</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[9px] font-mono text-slate-500">ACTIVE</span>
        </div>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-2 scroll-smooth">
        {allEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-600 space-y-2">
            <Activity className="w-8 h-8 opacity-30 animate-pulse" />
            <span className="text-[10px] uppercase tracking-widest font-bold">
              Monitoring Network...
            </span>
          </div>
        ) : (
          allEvents.map((evt, i) => {
            const colors = getLevelColor(evt.level);
            
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3 }}
                className={`p-3 rounded-lg border ${colors.bg} ${colors.border}`}
              >
                <div className="flex items-start gap-2">
                  <span className="text-[10px] font-mono text-slate-500 min-w-[60px]">
                    {evt.timestamp}
                  </span>
                  <span className="text-sm">{getLevelIcon(evt.level)}</span>
                  <span className={`flex-1 text-[11px] font-medium ${colors.text}`}>
                    {evt.message}
                  </span>
                </div>
                {evt.details && evt.details.attacker_ip && (
                  <div className="mt-2 pl-[72px] text-[10px] text-slate-500">
                    {evt.details.attacker_ip} → {evt.details.target_plc || evt.details.dst_ip}
                  </div>
                )}
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
}

// Main Monitor Page Component
export default function MonitorPage({ 
  events, 
  anomalyScore, 
  trafficData, 
  alertActive,
  playbookState,
  trapActive
}) {
  return (
    <div className="flex-1 flex flex-col min-w-0 bg-[#0a0b10] p-8 overflow-auto">
      <div className="max-w-[1600px] mx-auto w-full space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">Real-time Network Monitoring</h2>
            <p className="text-sm text-slate-400">
              Live telemetry from ICS network sensors and anomaly detection engine
            </p>
          </div>
          <div className={`px-4 py-2 rounded-lg border ${
            alertActive 
              ? 'bg-red-500/10 border-red-500/30 text-red-400' 
              : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
          }`}>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${alertActive ? 'bg-red-500 animate-pulse' : 'bg-emerald-500'}`} />
              <span className="text-xs font-bold uppercase tracking-wider">
                {alertActive ? 'INTRUSION DETECTED' : 'NOMINAL'}
              </span>
            </div>
          </div>
        </div>

        {/* Metrics Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <AnomalyGauge score={anomalyScore} />
          <TrafficSparkline data={trafficData} isAlert={alertActive} />
        </div>

        {/* Monitoring Streams */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <LiveEventStream 
            events={events} 
            playbookState={playbookState}
            alertActive={alertActive}
            trapActive={trapActive}
          />
          <PacketStream events={events} />
        </div>
      </div>
    </div>
  );
}
