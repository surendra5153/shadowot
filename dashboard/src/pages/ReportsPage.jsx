import React, { useEffect, useState } from 'react';
import IncidentHistory from '../components/IncidentHistory';

const API_BASE = import.meta.env.DEV ? 'http://localhost:3000' : window.location.origin;

export default function ReportsPage() {
  const [incidents, setIncidents] = useState([]);

  useEffect(() => {
    fetch(`${API_BASE}/api/incidents`).then(r => r.json()).then(setIncidents).catch(() => {});
  }, []);

  return (
    <div className="flex-1 p-6 overflow-auto">
      <h1 className="text-xl font-semibold mb-4">Incident Reports</h1>
      <IncidentHistory incidents={incidents} />
    </div>
  );
}
