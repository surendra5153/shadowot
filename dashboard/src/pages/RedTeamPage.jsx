import React, { useState, useEffect } from 'react';
import { Play, RotateCcw, AlertTriangle, CheckCircle, Activity } from 'lucide-react';

const RedTeamPage = () => {
  const [testResults, setTestResults] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [stats, setStats] = useState({
    totalTests: 0,
    detectionRate: 0,
    lastRetrain: 'Never'
  });

  const runTests = () => {
    setIsRunning(true);
    // Simulate running tests
    setTimeout(() => {
      const newResults = [
        { id: 1, template: 'slow_scan', detected: false, timestamp: new Date().toISOString() },
        { id: 2, template: 'fast_scan', detected: true, timestamp: new Date().toISOString() },
        { id: 3, template: 'targeted_write', detected: true, timestamp: new Date().toISOString() },
        { id: 4, template: 'register_flood', detected: true, timestamp: new Date().toISOString() },
        { id: 5, template: 'function_code_fuzz', detected: false, timestamp: new Date().toISOString() },
      ];
      setTestResults(newResults);
      setIsRunning(false);
      setStats({
        totalTests: stats.totalTests + 5,
        detectionRate: 60,
        lastRetrain: new Date().toLocaleTimeString()
      });
    }, 3000);
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-[#0F111A]">
      <div className="h-14 border-b border-slate-800 flex items-center justify-between px-6 bg-[#141720]">
        <h1 className="font-sans font-semibold text-lg tracking-tight">Self-Evolving Red Team</h1>
        <button 
          onClick={runTests}
          disabled={isRunning}
          className={`flex items-center gap-2 px-4 py-2 rounded-md font-bold text-sm transition-all
            ${isRunning ? 'bg-slate-700 text-slate-400 cursor-not-allowed' : 'bg-red-600 hover:bg-red-500 text-white shadow-lg shadow-red-600/20'}`}
        >
          {isRunning ? <RotateCcw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
          {isRunning ? 'RUNNING ATTACK SUITE...' : 'RUN TEST NOW'}
        </button>
      </div>

      <div className="flex-1 p-6 overflow-auto">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-3 gap-6">
            <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800">
              <div className="text-slate-500 text-xs font-bold uppercase mb-2">Detection Rate</div>
              <div className="text-3xl font-mono font-bold text-cyan-400">{stats.detectionRate}%</div>
              <div className="mt-4 h-2 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-cyan-500 transition-all duration-1000" style={{ width: `${stats.detectionRate}%` }} />
              </div>
            </div>
            <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800">
              <div className="text-slate-500 text-xs font-bold uppercase mb-2">Total Attacks Generated</div>
              <div className="text-3xl font-mono font-bold text-white">{stats.totalTests}</div>
              <div className="text-xs text-slate-500 mt-2">Across 5 templates</div>
            </div>
            <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800">
              <div className="text-slate-500 text-xs font-bold uppercase mb-2">Last Model Retrain</div>
              <div className="text-3xl font-mono font-bold text-amber-500">{stats.lastRetrain}</div>
              <div className="text-xs text-slate-500 mt-2">Triggered by missed attacks</div>
            </div>
          </div>

          {/* Results Table */}
          <div className="bg-slate-900/50 rounded-xl border border-slate-800 overflow-hidden">
            <div className="p-4 border-b border-slate-800 bg-slate-800/30 flex justify-between items-center">
              <h3 className="text-sm font-bold text-slate-300">RECENT ATTACK VARIATIONS</h3>
              <Activity className="w-4 h-4 text-slate-500" />
            </div>
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-800/10 text-slate-500 text-[10px] font-bold uppercase">
                  <th className="p-4">Template</th>
                  <th className="p-4">Timestamp</th>
                  <th className="p-4">Detection Status</th>
                  <th className="p-4">Action</th>
                </tr>
              </thead>
              <tbody className="text-sm">
                {testResults.map(res => (
                  <tr key={res.id} className="border-t border-slate-800/50 hover:bg-slate-800/20 transition-colors">
                    <td className="p-4 font-mono text-cyan-400">{res.template}</td>
                    <td className="p-4 text-slate-400">{res.timestamp}</td>
                    <td className="p-4">
                      {res.detected ? (
                        <span className="flex items-center gap-1 text-green-500">
                          <CheckCircle className="w-4 h-4" /> Detected
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-red-500">
                          <AlertTriangle className="w-4 h-4" /> Missed (Feedback Loop)
                        </span>
                      )}
                    </td>
                    <td className="p-4">
                      <button className="text-xs text-slate-500 hover:text-cyan-400 transition-colors underline">View Trace</button>
                    </td>
                  </tr>
                ))}
                {testResults.length === 0 && (
                  <tr>
                    <td colSpan="4" className="p-8 text-center text-slate-600 italic">No tests run in current session</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RedTeamPage;
