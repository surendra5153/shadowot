import React from 'react';

export default function ThreatIntelTicker({ iocs = [] }) {
  const text = (iocs.length ? iocs : ['No threat intel yet — system nominal']).join('   ◆   ');
  return (
    <div
      className="h-8 border-t border-[#334155] bg-[#111827] overflow-hidden flex items-center shrink-0 w-full"
      style={{ position: 'relative' }}
    >
      <span
        className="whitespace-nowrap text-xs text-amber-300"
        style={{
          display: 'inline-block',
          animation: 'marquee 30s linear infinite',
          paddingLeft: '100%',
        }}
      >
        {text}
      </span>
    </div>
  );
}
