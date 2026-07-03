import React from 'react';
import { Target } from 'lucide-react';

function TrapManagementPage() {
  return (
    <div className="flex-1 flex flex-col min-w-0 bg-[#0a0b10] p-8">
      <div className="flex items-center gap-4 mb-8">
        <div className="p-3 bg-cyan-500/10 rounded-lg border border-cyan-500/30">
          <Target className="w-6 h-6 text-cyan-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Trap Management Center</h1>
          <p className="text-sm text-slate-400">Deception Assets & Active Sessions</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="shadow-ot-card p-6">
          <div className="text-sm text-slate-400 mb-2">Active Traps</div>
          <div className="text-3xl font-bold text-cyan-400">3</div>
        </div>
        
        <div className="shadow-ot-card p-6">
          <div className="text-sm text-slate-400 mb-2">Attackers Redirected</div>
          <div className="text-3xl font-bold text-red-400">12</div>
        </div>
        
        <div className="shadow-ot-card p-6">
          <div className="text-sm text-slate-400 mb-2">Commands Captured</div>
          <div className="text-3xl font-bold text-emerald-400">847</div>
        </div>
        
        <div className="shadow-ot-card p-6">
          <div className="text-sm text-slate-400 mb-2">Detection Rate</div>
          <div className="text-3xl font-bold text-yellow-400">96%</div>
        </div>
      </div>

      <div className="mt-8 shadow-ot-card p-6">
        <h2 className="text-lg font-bold text-white mb-4">Coming Soon</h2>
        <p className="text-slate-400">
          The Trap Management page is currently under development. Features will include:
        </p>
        <ul className="mt-4 space-y-2 text-slate-300">
          <li>• Real-time trap deployment and monitoring</li>
          <li>• Attacker session tracking</li>
          <li>• Command capture and analysis</li>
          <li>• Adaptive trap generation</li>
          <li>• Deception network visualization</li>
        </ul>
      </div>
    </div>
  );
}

export default TrapManagementPage;
