import React, { useEffect, useState } from 'react';
import { Shield, Database, Activity, AlertTriangle, FileText, TrendingUp, Clock, Target } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = import.meta.env.DEV ? 'http://localhost:3000' : window.location.origin;

// Session Summary Panel Component
function SessionSummaryPanel({ session }) {
  if (!session || !session.active) {
    return (
      <div className="shadow-ot-card p-6">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-2">
          <Activity size={16} className="text-primary" />
          Current Session
        </h3>
        <div className="text-center py-8 text-slate-500">
          <Shield className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p className="text-sm">No active attack session</p>
        </div>
      </div>
    );
  }

  const getSeverityColor = (score) => {
    if (score >= 75) return 'text-red-400';
    if (score >= 50) return 'text-orange-400';
    if (score >= 25) return 'text-yellow-400';
    return 'text-emerald-400';
  };

  const getStatusColor = (status) => {
    if (status === 'CONTAINED') return 'text-emerald-400';
    if (status === 'PROFILING' || status === 'REPORT_GENERATING') return 'text-blue-400';
    return 'text-red-400';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="shadow-ot-card p-6 border-l-4 border-primary"
    >
      <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-2">
        <Activity size={16} className="text-primary animate-pulse" />
        Active Session
      </h3>

      <div className="space-y-4">
        {/* Session ID */}
        <div>
          <div className="text-xs text-slate-500 mb-1">Session ID</div>
          <div className="font-mono text-sm text-primary">{session.session_id}</div>
        </div>

        {/* Duration */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-xs text-slate-500 mb-1">Duration</div>
            <div className="font-mono text-lg font-bold text-white">{session.duration}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500 mb-1">Events</div>
            <div className="font-mono text-lg font-bold text-white">{session.event_count}</div>
          </div>
        </div>

        {/* Affected PLCs */}
        <div>
          <div className="text-xs text-slate-500 mb-1">Affected Systems</div>
          <div className="flex flex-wrap gap-1">
            {session.affected_plcs && session.affected_plcs.length > 0 ? (
              session.affected_plcs.map(plc => (
                <span key={plc} className="px-2 py-1 bg-red-500/10 text-red-400 text-xs rounded border border-red-500/30">
                  {plc}
                </span>
              ))
            ) : (
              <span className="text-slate-500 text-xs">None identified</span>
            )}
          </div>
        </div>

        {/* Threat Family */}
        <div>
          <div className="text-xs text-slate-500 mb-1">Detected Threat Family</div>
          <div className="font-semibold text-sm text-yellow-400">{session.threat_family}</div>
        </div>

        {/* Risk Score */}
        <div>
          <div className="text-xs text-slate-500 mb-1">Risk Score</div>
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${session.risk_score}%` }}
                transition={{ duration: 1 }}
                className={`h-full ${
                  session.risk_score >= 75 ? 'bg-red-500' :
                  session.risk_score >= 50 ? 'bg-orange-500' :
                  session.risk_score >= 25 ? 'bg-yellow-500' : 'bg-emerald-500'
                }`}
              />
            </div>
            <span className={`font-mono text-lg font-bold ${getSeverityColor(session.risk_score)}`}>
              {session.risk_score}
            </span>
          </div>
        </div>

        {/* Techniques Detected */}
        <div>
          <div className="text-xs text-slate-500 mb-1">ATT&CK Techniques</div>
          <div className="font-mono text-lg font-bold text-cyan-400">{session.technique_count}</div>
        </div>

        {/* Containment Status */}
        <div>
          <div className="text-xs text-slate-500 mb-1">Status</div>
          <div className={`font-bold text-sm ${getStatusColor(session.containment_status)}`}>
            {session.containment_status}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// Dynamic IOC List Component
function DynamicIOCList({ sessionId }) {
  const [iocs, setIocs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!sessionId) {
      setIocs([]);
      setLoading(false);
      return;
    }

    fetch(`${API_BASE}/api/session/${sessionId}/iocs`)
      .then(r => r.json())
      .then(data => {
        setIocs(data.iocs || []);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [sessionId]);

  const getSeverityBadge = (severity) => {
    const colors = {
      'CRITICAL': 'bg-red-500/10 text-red-400 border-red-500/30',
      'HIGH': 'bg-orange-500/10 text-orange-400 border-orange-500/30',
      'MEDIUM': 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
      'LOW': 'bg-slate-500/10 text-slate-400 border-slate-500/30'
    };
    return colors[severity] || colors['LOW'];
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'ipv4-addr': return '🌐';
      case 'behavior': return '⚠️';
      case 'register': return '📝';
      default: return '•';
    }
  };

  if (loading) {
    return (
      <div className="shadow-ot-card p-6">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
          Indicators of Compromise (IOCs)
        </h3>
        <div className="text-center py-8 text-slate-500">
          <div className="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full mx-auto" />
          <p className="text-sm mt-3">Loading IOCs...</p>
        </div>
      </div>
    );
  }

  if (iocs.length === 0) {
    return (
      <div className="shadow-ot-card p-6">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-2">
          <AlertTriangle size={16} className="text-primary" />
          Indicators of Compromise (IOCs)
        </h3>
        <div className="text-center py-8 text-slate-500">
          <Database className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p className="text-sm">No IOCs detected</p>
        </div>
      </div>
    );
  }

  return (
    <div className="shadow-ot-card p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <AlertTriangle size={16} className="text-primary" />
          Indicators of Compromise
        </h3>
        <span className="text-xs font-mono text-slate-500">{iocs.length} IOCs</span>
      </div>

      <div className="space-y-3 max-h-[500px] overflow-y-auto">
        {iocs.map((ioc, index) => (
          <motion.div
            key={ioc.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="p-4 rounded-lg border border-slate-700/50 bg-slate-800/30 hover:border-primary/30 transition-colors"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-lg">{getTypeIcon(ioc.type)}</span>
                <span className="font-mono text-xs font-bold text-primary">{ioc.id}</span>
              </div>
              <span className={`text-xs px-2 py-1 rounded border ${getSeverityBadge(ioc.severity)}`}>
                {ioc.severity}
              </span>
            </div>
            <div className="font-mono text-sm text-white mb-1">{ioc.value}</div>
            <div className="text-xs text-slate-400">{ioc.description}</div>
            {ioc.first_seen && (
              <div className="text-xs text-slate-600 mt-2">
                First seen: {new Date(ioc.first_seen).toLocaleString()}
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
}

// Bundle Details Modal Component
function BundleDetailsModal({ bundle, onClose }) {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (bundle) {
      fetch(`${API_BASE}/api/intel/bundle/${bundle.session_id}`)
        .then(r => r.json())
        .then(data => {
          setDetails(data);
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }
  }, [bundle]);

  if (!bundle) return null;

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-slate-900 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden border border-slate-700"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-slate-800/50 px-6 py-4 border-b border-slate-700 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">Bundle Details</h2>
            <p className="text-sm text-slate-400 font-mono">{bundle.session_id}</p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin w-12 h-12 border-2 border-primary border-t-transparent rounded-full mx-auto" />
              <p className="text-slate-400 mt-4">Loading bundle details...</p>
            </div>
          ) : details ? (
            <div className="space-y-6">
              {/* Summary */}
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 bg-slate-800/50 rounded-lg">
                  <div className="text-xs text-slate-500 mb-1">Indicators</div>
                  <div className="text-2xl font-bold text-primary">{details.indicators?.length || 0}</div>
                </div>
                <div className="p-4 bg-slate-800/50 rounded-lg">
                  <div className="text-xs text-slate-500 mb-1">Techniques</div>
                  <div className="text-2xl font-bold text-cyan-400">{details.attack_patterns?.length || 0}</div>
                </div>
                <div className="p-4 bg-slate-800/50 rounded-lg">
                  <div className="text-xs text-slate-500 mb-1">Severity</div>
                  <div className={`text-2xl font-bold ${
                    details.severity === 'CRITICAL' ? 'text-red-400' :
                    details.severity === 'HIGH' ? 'text-orange-400' :
                    details.severity === 'MEDIUM' ? 'text-yellow-400' : 'text-emerald-400'
                  }`}>{details.severity}</div>
                </div>
              </div>

              {/* Threat Actor */}
              {details.threat_actors && details.threat_actors.length > 0 && (
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-3">Threat Actor</h3>
                  <div className="p-4 bg-slate-800/30 rounded-lg border border-slate-700">
                    <div className="font-bold text-yellow-400 mb-2">{details.threat_actors[0].name}</div>
                    <div className="text-sm text-slate-300">{details.threat_actors[0].description}</div>
                  </div>
                </div>
              )}

              {/* ATT&CK Techniques */}
              {details.attack_patterns && details.attack_patterns.length > 0 && (
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-3">
                    ATT&CK Techniques ({details.attack_patterns.length})
                  </h3>
                  <div className="space-y-2">
                    {details.attack_patterns.map((tech, i) => (
                      <div key={i} className="p-3 bg-slate-800/30 rounded-lg border border-slate-700">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-mono text-xs font-bold text-primary">{tech.id}</span>
                          <span className="text-sm font-semibold text-white">{tech.name}</span>
                        </div>
                        <div className="text-xs text-slate-400">{tech.description}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Indicators */}
              {details.indicators && details.indicators.length > 0 && (
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-3">
                    Indicators ({details.indicators.length})
                  </h3>
                  <div className="space-y-2">
                    {details.indicators.map((ind, i) => (
                      <div key={i} className="p-3 bg-slate-800/30 rounded-lg border border-slate-700">
                        <div className="font-mono text-xs text-slate-500 mb-1">{ind.id}</div>
                        <div className="text-sm text-white font-semibold mb-1">{ind.name}</div>
                        <div className="text-xs text-slate-400 font-mono">{ind.pattern}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500">
              <p>Failed to load bundle details</p>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}

// Main Threat Intel Page Component
export default function IntelPage() {
  const [feedStatus, setFeedStatus] = useState({ enabled: 'false', count: 0, sample: [] });
  const [bundles, setBundles] = useState([]);
  const [selectedBundle, setSelectedBundle] = useState(null);
  const [currentSession, setCurrentSession] = useState(null);

  useEffect(() => {
    // Fetch feed status
    fetch(`${API_BASE}/api/intel/feed-status`)
      .then(r => r.json())
      .then(setFeedStatus)
      .catch(() => {});

    // Fetch bundles
    fetch(`${API_BASE}/api/intel/bundles`)
      .then(r => r.json())
      .then(d => setBundles(d.bundles || []))
      .catch(() => {});

    // Fetch current session
    fetch(`${API_BASE}/api/session/current`)
      .then(r => r.json())
      .then(setCurrentSession)
      .catch(() => {});

    // Refresh periodically
    const interval = setInterval(() => {
      fetch(`${API_BASE}/api/session/current`)
        .then(r => r.json())
        .then(setCurrentSession)
        .catch(() => {});
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getSeverityBadge = (severity) => {
    const colors = {
      'CRITICAL': 'bg-red-500/10 text-red-400 border-red-500/30',
      'HIGH': 'bg-orange-500/10 text-orange-400 border-orange-500/30',
      'MEDIUM': 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
      'LOW': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
    };
    return colors[severity] || colors['LOW'];
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-[#0a0b10] p-8 overflow-auto">
      <div className="max-w-[1600px] mx-auto w-full space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Threat Intelligence</h1>
          <p className="text-sm text-slate-400">
            STIX 2.1 threat intelligence bundles with ATT&CK for ICS technique mapping
          </p>
        </div>

        {/* Top Row: Session Summary + Feed Status */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Session Summary - 2 columns */}
          <div className="lg:col-span-2">
            <SessionSummaryPanel session={currentSession} />
          </div>

          {/* Feed Status */}
          <div className="shadow-ot-card p-6">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-2">
              <TrendingUp size={16} className="text-primary" />
              External Feeds
            </h3>
            <div className="space-y-3">
              <div>
                <div className="text-xs text-slate-500 mb-1">CISA AIS Feed</div>
                <div className={`text-sm font-semibold ${feedStatus.enabled === 'true' ? 'text-emerald-400' : 'text-slate-500'}`}>
                  {feedStatus.enabled === 'true' ? 'Enabled' : 'Disabled'}
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Incoming IOCs</div>
                <div className="text-2xl font-bold text-primary">{feedStatus.count}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Middle Row: IOCs for Current Session */}
        {currentSession && currentSession.active && (
          <DynamicIOCList sessionId={currentSession.session_id} />
        )}

        {/* Published Bundles */}
        <div className="shadow-ot-card p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <FileText size={16} className="text-primary" />
              Published STIX Bundles
            </h3>
            <span className="text-xs font-mono text-slate-500">{bundles.length} bundles</span>
          </div>

          {bundles.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <Database className="w-16 h-16 mx-auto mb-4 opacity-30" />
              <p className="text-sm">No threat intelligence bundles published yet</p>
              <p className="text-xs mt-2">Bundles are generated after attack containment</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {bundles.map((bundle, index) => (
                <motion.div
                  key={bundle.filename}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  onClick={() => setSelectedBundle(bundle)}
                  className="p-4 rounded-lg border border-slate-700 bg-slate-800/30 hover:border-primary/50 cursor-pointer transition-all hover:shadow-lg hover:shadow-primary/10"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Shield size={16} className="text-primary" />
                      <span className="text-xs font-mono text-slate-400">
                        {bundle.session_id.substring(0, 12)}...
                      </span>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded border ${getSeverityBadge(bundle.severity)}`}>
                      {bundle.severity}
                    </span>
                  </div>

                  <div className="space-y-2 mb-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-500">Indicators:</span>
                      <span className="font-bold text-primary">{bundle.indicator_count}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-500">Techniques:</span>
                      <span className="font-bold text-cyan-400">{bundle.technique_count}</span>
                    </div>
                  </div>

                  <div className="text-xs text-slate-400 truncate mb-2">
                    {bundle.threat_actor}
                  </div>

                  {bundle.timestamp && (
                    <div className="text-xs text-slate-600 flex items-center gap-1">
                      <Clock size={10} />
                      {new Date(bundle.timestamp).toLocaleString()}
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Bundle Details Modal */}
      <AnimatePresence>
        {selectedBundle && (
          <BundleDetailsModal
            bundle={selectedBundle}
            onClose={() => setSelectedBundle(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
