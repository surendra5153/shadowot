import React from 'react';
import { AreaChart, Area, ResponsiveContainer, YAxis, Tooltip } from 'recharts';
import { Activity } from 'lucide-react';

export default function TrafficSparkline({ data, isAlert }) {
  const color = isAlert ? '#ef4444' : '#4cd7f6';
  const glowColor = isAlert ? 'rgba(239, 68, 68, 0.2)' : 'rgba(76, 215, 246, 0.2)';

  return (
    <div className="shadow-ot-card h-32 w-full relative bg-gradient-to-br from-[#161a27] to-transparent p-6 flex flex-col justify-between">
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center gap-2">
          <Activity size={12} className={isAlert ? 'text-red-500' : 'text-primary'} />
          <span className="text-label-caps text-slate-400">Netflow Telemetry</span>
        </div>
        <div className="flex items-baseline gap-1">
          <span className={`text-lg font-mono font-bold tracking-tighter ${isAlert ? 'text-red-500' : 'text-primary'}`}>
            {data[data.length - 1]?.rate.toFixed(1)}
          </span>
          <span className="text-[9px] font-bold text-slate-600 uppercase">pps</span>
        </div>
      </div>

      <div className="h-12 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorRate" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={color} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <YAxis hide domain={['dataMin - 5', 'dataMax + 5']} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', fontSize: '10px' }}
              itemStyle={{ color: color }}
            />
            <Area 
              type="monotone" 
              dataKey="rate" 
              stroke={color} 
              fillOpacity={1} 
              fill="url(#colorRate)" 
              strokeWidth={2}
              isAnimationActive={true}
              animationDuration={1000}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      
      {/* Subtle indicator dots */}
      <div className="flex gap-1 justify-end">
        {[1, 2, 3].map(i => (
          <div key={i} className={`w-1 h-1 rounded-full ${isAlert ? 'bg-red-500/30' : 'bg-primary/30'}`} />
        ))}
      </div>
    </div>
  );
}
