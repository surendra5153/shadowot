import React from 'react';
import { Loader2, FileDown } from 'lucide-react';

const API_BASE = import.meta.env.DEV ? 'http://localhost:3000' : window.location.origin;

export default function ReportPanel({ sessionId, reportReady, reportPath }) {
  const downloadUrl = sessionId ? `${API_BASE}/api/report/${sessionId}` : null;

  return (
    <div className="shadow-ot-card p-4 space-y-3">
      <h3 className="font-semibold">Incident Report</h3>
      {!reportReady ? (
        <div className="flex items-center gap-2 text-amber-400 text-sm">
          <Loader2 size={14} className="animate-spin" /> Report generating...
        </div>
      ) : (
        <div className="space-y-2">
          <a
            href={downloadUrl || reportPath}
            className="inline-flex items-center gap-2 px-5 py-2 bg-primary text-on-primary font-semibold text-sm"
          >
            <FileDown size={16} />
            Download PDF
          </a>
          <button
            onClick={() => {}}
            className="ml-2 px-4 py-2 border border-primary text-primary text-sm"
          >
            Publish to TAXII
          </button>
        </div>
      )}
    </div>
  );
}
