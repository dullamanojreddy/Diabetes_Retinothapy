import React from 'react';
import { FileText, Printer, Download, Clock, Zap, ExternalLink } from 'lucide-react';
import { TimingInfo } from '../types/prediction';

interface ReportActionsProps {
  screeningId: string;
  timing?: TimingInfo;
}

export const ReportActions: React.FC<ReportActionsProps> = ({ screeningId, timing }) => {
  const reportUrl = `/api/reports/${screeningId}`;
  const jsonUrl = `/api/reports/${screeningId}/json`;

  const handlePrint = () => {
    const printWindow = window.open(reportUrl, '_blank');
    if (printWindow) {
      printWindow.focus();
    }
  };

  return (
    <div className="card-glass border border-surface-800/80 rounded-2xl p-6 shadow-xl space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-surface-800">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-brand-950/60 border border-brand-800/80 text-brand-400">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-surface-100 flex items-center gap-2">
              Automated Clinical Report & Export
              <span className="text-xs px-2 py-0.5 rounded-full bg-brand-950 text-brand-300 border border-brand-800/60 font-mono">Phase 8</span>
            </h3>
            <p className="text-xs text-surface-400">Print-ready multimodal screening documentation and EMR telemetry export</p>
          </div>
        </div>

        {/* Phase 10 Monotonic Timing Badges */}
        {timing && (
          <div className="flex items-center space-x-2 text-xs font-mono text-surface-300 bg-surface-900/80 px-3 py-1.5 rounded-lg border border-surface-800">
            <Clock className="w-3.5 h-3.5 text-brand-400" />
            <span>Total: {timing.total_pipeline_ms.toFixed(0)}ms</span>
            <span className="text-surface-600">&bull;</span>
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span>Model: {timing.inference_ms.toFixed(0)}ms</span>
            {timing.is_warmup && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800 font-bold">Cold Start</span>
            )}
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-3 pt-1">
        <a
          href={reportUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs transition-all shadow-lg hover:shadow-brand-500/20"
        >
          <FileText className="w-4 h-4" />
          <span>View Screening Report</span>
          <ExternalLink className="w-3.5 h-3.5 ml-0.5 opacity-80" />
        </a>

        <button
          onClick={handlePrint}
          className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-100 font-semibold text-xs border border-surface-700 transition-all"
        >
          <Printer className="w-4 h-4 text-surface-400" />
          <span>Print / Save PDF</span>
        </button>

        <a
          href={jsonUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-300 font-semibold text-xs border border-surface-700 transition-all"
        >
          <Download className="w-4 h-4 text-surface-400" />
          <span>Export JSON Telemetry</span>
        </a>
      </div>
    </div>
  );
};
