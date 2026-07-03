import React from 'react';
import { motion } from 'framer-motion';

export default function NetworkTopology({ alertActive, trapActive }) {
  // Balanced deterministic coordinates
  const nodes = {
    hmi: { x: 120, y: 150, label: 'HMI', type: 'hmi' },
    plc1: { x: 320, y: 90, label: 'PLC-01', type: 'plc' },
    plc2: { x: 320, y: 210, label: 'PLC-02', type: 'plc' },
    attacker: { x: 60, y: 60, label: 'ATTACKER', type: 'attacker' },
    trap: { x: 320, y: 150, label: 'TRAP-01', type: 'trap' }
  };

  const drawCurve = (x1, y1, x2, y2, color, dashed = false) => {
    // Control point for subtle curve
    const cx = (x1 + x2) / 2;
    const path = `M ${x1} ${y1} Q ${cx} ${y1} ${x2} ${y2}`;
    
    return (
      <path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeDasharray={dashed ? "4 4" : "none"}
        style={{ transition: 'all 0.5s ease-in-out' }}
      />
    );
  };

  // Animated traffic flow particles
  const TrafficParticle = ({ path, color, delay = 0 }) => (
    <motion.circle
      r="3"
      fill={color}
      filter="url(#glow)"
      initial={{ offsetDistance: '0%', opacity: 0 }}
      animate={{ 
        offsetDistance: ['0%', '100%'],
        opacity: [0, 1, 1, 0]
      }}
      transition={{
        duration: 2,
        repeat: Infinity,
        delay: delay,
        ease: "linear"
      }}
      style={{ offsetPath: `path('${path}')` }}
    >
      <animateMotion
        dur="2s"
        repeatCount="indefinite"
        begin={`${delay}s`}
        path={path}
      />
    </motion.circle>
  );

  // Get node status color
  const getNodeStatus = (key) => {
    if (key === 'attacker') return { color: '#ef4444', label: 'THREAT', ring: true };
    if (key === 'trap' && trapActive) return { color: '#4cd7f6', label: 'DECEPTION', ring: true };
    if (key === 'plc1' && alertActive && !trapActive) return { color: '#ef4444', label: 'UNDER ATTACK', ring: true };
    if (key === 'hmi') return { color: '#10b981', label: 'NORMAL', ring: false };
    return { color: '#10b981', label: 'NORMAL', ring: false };
  };

  return (
    <div className="shadow-ot-card h-80 w-full relative flex items-center justify-center p-4 overflow-hidden bg-gradient-to-br from-slate-900/50 to-slate-950/50">
      <div className="absolute top-3 left-4 text-label-caps text-on-surface-variant z-10 flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
        NETWORK TOPOLOGY
      </div>
      
      {/* Status Legend */}
      <div className="absolute top-3 right-4 flex gap-3 text-[9px] z-10">
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-emerald-500" />
          <span className="text-slate-400 uppercase tracking-wider">Normal</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-red-500" />
          <span className="text-slate-400 uppercase tracking-wider">Attack</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-cyan-400" />
          <span className="text-slate-400 uppercase tracking-wider">Deception</span>
        </div>
      </div>
      
      <svg className="w-full h-full max-w-md mt-8" viewBox="0 0 400 300" preserveAspectRatio="xMidYMid meet">
        <defs>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          <filter id="strongGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Internal Network Connections */}
        {drawCurve(nodes.hmi.x, nodes.hmi.y, nodes.plc1.x, nodes.plc1.y, "#334155")}
        {drawCurve(nodes.hmi.x, nodes.hmi.y, nodes.plc2.x, nodes.plc2.y, "#334155")}
        
        {/* Attack Path: ATTACKER → PLC-01 */}
        {alertActive && !trapActive && (
          <g>
            {drawCurve(nodes.attacker.x, nodes.attacker.y, nodes.plc1.x, nodes.plc1.y, "#ef4444", true)}
            <TrafficParticle 
              path={`M ${nodes.attacker.x} ${nodes.attacker.y} Q ${(nodes.attacker.x + nodes.plc1.x) / 2} ${nodes.attacker.y} ${nodes.plc1.x} ${nodes.plc1.y}`}
              color="#ef4444"
              delay={0}
            />
            <TrafficParticle 
              path={`M ${nodes.attacker.x} ${nodes.attacker.y} Q ${(nodes.attacker.x + nodes.plc1.x) / 2} ${nodes.attacker.y} ${nodes.plc1.x} ${nodes.plc1.y}`}
              color="#ef4444"
              delay={0.6}
            />
          </g>
        )}
        
        {/* Deception Path: PLC-01 → TRAP-01 (redirect) */}
        {trapActive && (
          <g>
            {/* Attacker still tries to reach PLC but gets redirected */}
            {drawCurve(nodes.attacker.x, nodes.attacker.y, nodes.plc1.x, nodes.plc1.y, "#64748b", true)}
            {/* Redirect to trap */}
            {drawCurve(nodes.plc1.x, nodes.plc1.y, nodes.trap.x, nodes.trap.y, "#4cd7f6", true)}
            <TrafficParticle 
              path={`M ${nodes.plc1.x} ${nodes.plc1.y} Q ${(nodes.plc1.x + nodes.trap.x) / 2} ${nodes.plc1.y} ${nodes.trap.x} ${nodes.trap.y}`}
              color="#4cd7f6"
              delay={0}
            />
            <TrafficParticle 
              path={`M ${nodes.plc1.x} ${nodes.plc1.y} Q ${(nodes.plc1.x + nodes.trap.x) / 2} ${nodes.plc1.y} ${nodes.trap.x} ${nodes.trap.y}`}
              color="#4cd7f6"
              delay={0.7}
            />
          </g>
        )}

        {/* Nodes */}
        {Object.entries(nodes).map(([key, node]) => {
          if (key === 'attacker' && !alertActive) return null;
          if (key === 'trap' && !trapActive) return null;
          
          const status = getNodeStatus(key);
          const r = (key === 'hmi' || key === 'attacker' || key === 'trap') ? 16 : 14;

          return (
            <g key={key}>
              {/* Pulsing ring for active/attacked nodes */}
              {status.ring && (
                <motion.circle
                  cx={node.x}
                  cy={node.y}
                  r={r + 8}
                  fill="none"
                  stroke={status.color}
                  strokeWidth="2"
                  strokeOpacity="0.3"
                  animate={{ 
                    r: [r + 8, r + 14, r + 8],
                    strokeOpacity: [0.3, 0, 0.3]
                  }}
                  transition={{ 
                    duration: 2, 
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                />
              )}
              
              {/* Outer glow */}
              <circle 
                cx={node.x} 
                cy={node.y} 
                r={r + 4} 
                fill={status.color} 
                fillOpacity="0.15" 
                filter="url(#glow)" 
              />
              
              {/* Node circle */}
              <motion.circle 
                cx={node.x} 
                cy={node.y} 
                r={r} 
                fill="#0f172a" 
                stroke={status.color} 
                strokeWidth="3"
                initial={false}
                animate={{ 
                  strokeWidth: status.ring ? [3, 4, 3] : 3
                }}
                transition={{ 
                  duration: 1.5, 
                  repeat: status.ring ? Infinity : 0 
                }}
              />
              
              {/* Node type indicator */}
              <text 
                x={node.x} 
                y={node.y + 1} 
                textAnchor="middle" 
                fill={status.color}
                className="font-bold"
                style={{ 
                  fontFamily: 'monospace', 
                  fontSize: '10px'
                }}
              >
                {key === 'hmi' ? 'H' : key === 'attacker' ? '⚠' : key === 'trap' ? 'T' : 'P'}
              </text>
              
              {/* Node label */}
              <text 
                x={node.x} 
                y={node.y + r + 18} 
                textAnchor="middle" 
                fill={status.color} 
                className="text-label-caps" 
                style={{ 
                  fontFamily: 'Outfit, sans-serif', 
                  fontSize: '9px', 
                  letterSpacing: '0.08em',
                  fontWeight: 700
                }}
              >
                {node.label}
              </text>
              
              {/* Status label */}
              <text 
                x={node.x} 
                y={node.y + r + 28} 
                textAnchor="middle" 
                fill={status.color}
                fillOpacity="0.6"
                style={{ 
                  fontFamily: 'monospace', 
                  fontSize: '7px', 
                  letterSpacing: '0.05em',
                  fontWeight: 600
                }}
              >
                {status.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
