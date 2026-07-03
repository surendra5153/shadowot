import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { io } from 'socket.io-client';
import { Server, Activity, Shield, Settings, Menu, Dna, Zap, FileText, Radio } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

import MetricCards from './components/MetricCards';
import NetworkTopology from './components/NetworkTopology';
import EventLog from './components/EventLog';
import AnomalyGauge from './components/AnomalyGauge';
import TrafficSparkline from './components/TrafficSparkline';
import KillChainBar from './components/KillChainBar';
import ProfilerPage from './pages/ProfilerPage';
import RedTeamPage from './pages/RedTeamPage';
import ReportsPage from './pages/ReportsPage';
import IntelPage from './pages/IntelPage';
import MonitorPage from './pages/MonitorPage';
import SOARStatus from './components/SOARStatus';
import ReportPanel from './components/ReportPanel';
import ThreatIntelTicker from './components/ThreatIntelTicker';
import DemoLauncher from './components/DemoLauncher';
import TrapManagementPage from './pages/TrapManagementPage.jsx';

const socketUrl = import.meta.env.DEV ? 'http://localhost:3000' : window.location.origin;
const socket    = io(socketUrl);

// ── Navigation sidebar ────────────────────────────────────────────────────────

function NavItem({ to, icon: Icon, label }) {
  return (
    <NavLink to={to} className="group relative flex items-center justify-center py-2">
      {({ isActive }) => (
        <>
          <div className={`absolute left-0 w-1 rounded-r-full transition-all duration-300 ${isActive ? 'h-6 bg-primary shadow-[0_0_10px_var(--primary-glow)]' : 'h-0 bg-slate-500'}`} />
          <Icon
            className={`w-5 h-5 cursor-pointer transition-all duration-300 transform group-hover:scale-110
              ${isActive ? 'text-primary' : 'text-slate-500 group-hover:text-slate-300'}`}
          />
          <div className="absolute left-14 px-2 py-1 bg-slate-800 text-white text-[10px] rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50 uppercase tracking-widest border border-slate-700">
            {label}
          </div>
        </>
      )}
    </NavLink>
  );
}

function Sidebar() {
  return (
    <div className="w-16 bg-[#0f172a] border-r border-white/5 flex flex-col items-center py-6 space-y-8 flex-shrink-0 z-50">
      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center shadow-lg shadow-primary/20 mb-4 cursor-pointer hover:rotate-12 transition-transform">
        <Shield className="w-6 h-6 text-white" />
      </div>
      <div className="flex flex-col space-y-4 w-full">
        <NavItem to="/"        icon={Server}   label="Overview" />
        <NavItem to="/monitor" icon={Activity}  label="Network Monitor"   />
        <NavItem to="/traps"   icon={Zap}       label="Active Traps"     />
        <NavItem to="/profiler" icon={Dna}      label="DNA Behavioral Profiler" />
        <NavItem to="/red-team" icon={Zap}      label="Red Team Testing" />
        <NavItem to="/reports" icon={FileText}  label="Incident Reports" />
        <NavItem to="/intel" icon={Radio}       label="Threat Intelligence" />
      </div>
      <div className="flex-grow" />
      <div className="p-4 border-t border-white/5 w-full flex justify-center">
        <Settings className="w-5 h-5 text-slate-500 cursor-pointer hover:text-primary transition-colors" />
      </div>
    </div>
  );
}

// ── Dashboard page ────────────────────────────────────────────────────────────

function DashboardPage({
  status, nodesOnline, threats, traps, uptime,
  events, anomalyScore, trafficData, alertActive, trapActive,
  killChainStage, confirmedTechniques, playbookState, sessionId, reportReady, reportPath,
  riskScore, riskLevel, playbookTimeline
}) {
  return (
    <div className="flex-1 flex flex-col min-w-0 bg-[#0a0b10] bg-[radial-gradient(circle_at_top_right,rgba(76,215,246,0.05),transparent_40%)]">
      {/* Top bar */}
      <header className="h-16 border-b border-white/5 flex items-center justify-between px-8 bg-[#0f172a]/50 backdrop-blur-md sticky top-0 z-40">
        <div className="flex items-center space-x-4">
          <div className="flex flex-col">
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-3">
              SHADOW-OT <span className="text-[10px] font-mono text-primary bg-primary/10 px-2 py-0.5 rounded border border-primary/20">V2.4.1</span>
            </h1>
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-[0.2em]">Autonomous Deception & Anomaly Grid</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-6">
          <div className="flex flex-col items-end">
            <span className="font-mono text-xs text-slate-400">SYSTEM_CLOCK</span>
            <span className="font-mono text-sm text-primary">
              {new Date().toISOString().split('T')[1].split('.')[0]} <span className="text-[10px] text-slate-500">UTC</span>
            </span>
          </div>
          
          <div className={`h-10 px-4 border rounded-xl flex items-center gap-3 transition-all duration-500 shadow-lg
            ${status === 'NOMINAL'
              ? 'bg-emerald-500/5 border-emerald-500/20 text-emerald-500 shadow-emerald-500/5'
              : 'bg-red-500/10 border-red-500/30 text-red-500 shadow-red-500/10'}`}>
            <div className="relative">
              <div className={`w-2 h-2 rounded-full ${status === 'NOMINAL' ? 'bg-emerald-500' : 'bg-red-500 animate-ping absolute'}`} />
              <div className={`w-2 h-2 rounded-full ${status === 'NOMINAL' ? 'bg-emerald-500' : 'bg-red-500 relative'}`} />
            </div>
            <span className="text-xs font-bold tracking-widest uppercase">{status}</span>
          </div>
        </div>
      </header>

      {/* Dashboard grid */}
      <main className="flex-1 p-8 overflow-auto">
        <div className="max-w-[1600px] mx-auto space-y-8">
          <MetricCards
            status={status} nodesOnline={nodesOnline}
            threats={threats} traps={traps} uptime={uptime}
            riskScore={riskScore} riskLevel={riskLevel}
          />
          
          <div className="grid grid-cols-12 gap-8">
            <div className="col-span-12 lg:col-span-8 space-y-8">
              <KillChainBar currentStage={killChainStage} confirmedTechniques={confirmedTechniques} />
              <NetworkTopology alertActive={alertActive} trapActive={trapActive} />
              
              <div className="grid grid-cols-2 gap-8">
                <AnomalyGauge score={anomalyScore} />
                <TrafficSparkline data={trafficData} isAlert={alertActive} />
              </div>
            </div>
            
            <div className="col-span-12 lg:col-span-4 space-y-8">
              <SOARStatus currentState={playbookState} timeline={playbookTimeline} />
              <ReportPanel sessionId={sessionId} reportReady={reportReady} reportPath={reportPath} />
              <EventLog events={events} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

// ── Root App ──────────────────────────────────────────────────────────────────

function App() {
  const [status, setStatus]         = useState("NOMINAL");
  const [nodesOnline, setNodesOnline] = useState(3);
  const [threats, setThreats]       = useState(0);
  const [traps, setTraps]           = useState(1);  // Start at 1 baseline trap
  const [uptime, setUptime]         = useState(0);
  const [riskScore, setRiskScore]   = useState(0);
  const [riskLevel, setRiskLevel]   = useState("Low");
  const [events, setEvents]         = useState([]);
  const [anomalyScore, setAnomalyScore] = useState(0);
  const [trafficData, setTrafficData]   = useState(Array(60).fill({ rate: 50 }));
  const [trapActive, setTrapActive]     = useState(false);
  const [alertActive, setAlertActive]   = useState(false);
  const [killChainStage, setKillChainStage] = useState('initial-access');
  const [confirmedTechniques, setConfirmedTechniques] = useState([]);
  const [playbookState, setPlaybookState] = useState('IDLE');
  const [playbookTimeline, setPlaybookTimeline] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [reportReady, setReportReady] = useState(false);
  const [reportPath, setReportPath] = useState('');
  const [tickerIocs, setTickerIocs] = useState([]);

  useEffect(() => {
    const timer = setInterval(() => setUptime(u => u + 1), 1000);
    
    // Enhanced traffic simulation with realistic patterns
    const trafficTimer = setInterval(() => {
      setTrafficData(prev => {
        const newData = [...prev.slice(1)];
        const lastRate = prev[prev.length - 1].rate;
        
        // Baseline: stable around 50-55 pps
        let targetRate = 52;
        let variance = 2;
        
        // During alert: spike to 80-100 pps
        if (alertActive && !trapActive) {
          targetRate = 90;
          variance = 10;
        }
        // After trap deployment: drop back to 55-60 pps (slightly elevated)
        else if (trapActive) {
          targetRate = 57;
          variance = 3;
        }
        
        // Smooth transition toward target
        const drift = (targetRate - lastRate) * 0.15; // 15% correction per tick
        const randomWalk = (Math.random() - 0.5) * variance;
        const newRate = Math.max(30, Math.min(120, lastRate + drift + randomWalk));
        
        newData.push({ rate: newRate });
        return newData;
      });
    }, 1000);

    fetch(`${socketUrl}/api/status`)
      .then(r => r.json())
      .then(d => {
        setStatus(d.status);
        setNodesOnline(d.nodes_online);
        setThreats(d.threats_detected);
        setTraps(d.traps_active);
        setRiskScore(d.risk_score || 0);
        setRiskLevel(d.risk_level || "Low");
      }).catch(() => {});

    fetch(`${socketUrl}/api/events`)
      .then(r => r.json())
      .then(d => setEvents(d)).catch(() => {});

    socket.on('packet_rate', () => {
      setTrafficData(prev => {
        const newData  = [...prev.slice(1)];
        const lastRate = prev[prev.length - 1].rate;
        newData.push({ rate: lastRate + 1 });
        return newData;
      });
    });

    socket.on('anomaly_score', (data) => {
      setAnomalyScore(data.score);
    });

    socket.on('risk_update', (data) => {
      setRiskScore(data.risk_score);
      setRiskLevel(data.risk_level);
    });

    socket.on('alert', (data) => {
      setStatus("INTRUSION DETECTED");
      setThreats(t => t + 1);
      setAlertActive(true);
      setTickerIocs(prev => [`ALERT: ${data.trigger} detected on ${data.target_plc}`, ...prev].slice(0, 12));
    });

    socket.on('trap_deployed', (data) => {
      setTraps(t => t + 1);
      setTrapActive(true);
      const targetIp = data.trap_ip || data.target_plc || '10.5.0.100';
      setTickerIocs(prev => [`TRAP_DEPLOYED: Rerouted attacker to ${targetIp}`, ...prev].slice(0, 12));
    });

    socket.on('event_log', (data) => {
      setEvents(prev => [...prev, data].slice(-50));
    });

    socket.on('attck_update', (data) => {
      setKillChainStage(data.summary.current_stage);
      setConfirmedTechniques(data.summary.confirmed_details);
    });
    socket.on('playbook_update', (data) => {
      setPlaybookState(data.state || 'IDLE');
      if (data.session_id) setSessionId(data.session_id);
      if (data.state === 'REPORT_GENERATING') setReportReady(false);
      if (data.timeline) setPlaybookTimeline(data.timeline);
    });
    socket.on('report_ready', (data) => {
      setSessionId(data.session_id);
      setReportReady(true);
      setReportPath(data.report_path);
      setTickerIocs(prev => [`REPORT_READY:${data.session_id}`, ...prev].slice(0, 12));
    });

    socket.on('system_reset', () => {
      setStatus("NOMINAL");
      setThreats(0);
      setTraps(1);  // Reset to baseline
      setRiskScore(0);
      setRiskLevel("Low");
      setEvents([]);
      setAlertActive(false);
      setTrapActive(false);
      setKillChainStage(null);
      setConfirmedTechniques([]);
      setPlaybookState("IDLE");
      setPlaybookTimeline([]);
      setSessionId(null);
      setReportReady(false);
      setReportPath(null);
    });

    return () => {
      clearInterval(timer);
      clearInterval(trafficTimer);
    };
  }, []);

  return (
    <BrowserRouter>
      <div className="flex h-screen bg-background text-on-surface">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <div className="flex-1 overflow-auto flex flex-col">
            <AnimatePresence mode="wait">
              <Routes>
                <Route
                  path="/"
                  element={
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 flex flex-col min-h-0">
                      <DashboardPage
                        status={status} nodesOnline={nodesOnline}
                        threats={threats} traps={traps} uptime={uptime}
                        events={events} anomalyScore={anomalyScore}
                        trafficData={trafficData}
                        alertActive={alertActive} trapActive={trapActive}
                        killChainStage={killChainStage}
                        confirmedTechniques={confirmedTechniques}
                        playbookState={playbookState}
                        playbookTimeline={playbookTimeline}
                        sessionId={sessionId}
                        reportReady={reportReady}
                        reportPath={reportPath}
                        riskScore={riskScore}
                        riskLevel={riskLevel}
                      />
                    </motion.div>
                  }
                />
                <Route path="/profiler" element={<ProfilerPage socket={socket} />} />
                <Route path="/red-team" element={<RedTeamPage />} />
                <Route path="/reports" element={<ReportsPage />} />
                <Route path="/intel" element={<IntelPage />} />
            {/* Stubs for sidebar links */}
                <Route path="/monitor" element={
                  <MonitorPage 
                    events={events}
                    anomalyScore={anomalyScore}
                    trafficData={trafficData}
                    alertActive={alertActive}
                    playbookState={playbookState}
                    trapActive={trapActive}
                  />
                } />
                <Route path="/traps" element={<TrapManagementPage socket={socket} />} />
              </Routes>
            </AnimatePresence>
          </div>
          <ThreatIntelTicker iocs={tickerIocs} />
        </div>
      </div>
      <DemoLauncher socket={socket} />
    </BrowserRouter>
  );
}

export default App;
