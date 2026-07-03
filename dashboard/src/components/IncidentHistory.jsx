import React from 'react';

const API_BASE = import.meta.env.DEV ? 'http://localhost:3000' : window.location.origin;

export default function IncidentHistory({ incidents = [] }) {
  return (
    <div className="shadow-ot-card p-4">
      <table className="w-full text-sm">
        <thead className="text-on-surface-variant">
          <tr>
            <th className="text-left py-2">Session</th>
            <th className="text-left py-2">Severity</th>
            <th className="text-left py-2">Duration</th>
            <th className="text-left py-2">APT Match</th>
            <th className="text-left py-2">Report</th>
          </tr>
        </thead>
        <tbody>
          {incidents.map((i) => (
            <tr key={i.session_id} className="border-t border-card-border">
              <td className="py-2 font-mono text-xs">{i.session_id}</td>
              <td className="py-2">{i.severity}</td>
              <td className="py-2">{i.duration}</td>
              <td className="py-2">{i.profile?.apt_match || 'Unknown'}</td>
              <td className="py-2">
                <a className="text-primary underline font-semibold" href={`${API_BASE}/api/report/${i.session_id}`}>
                  Download PDF
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
