import React from 'react';
import { FileText, Printer, Clock, Cpu, CheckCircle2, ShieldCheck, Check } from 'lucide-react';
import { PredictionResponse } from '../types/prediction';
import { formatDate, formatPercent, getSeverityStyle } from '../utils/formatting';

interface ScreeningSummaryProps {
  result: PredictionResponse;
}

export const ScreeningSummary: React.FC<ScreeningSummaryProps> = ({ result }) => {
  const prediction = result.diagnosis || result.prediction || {
    class_id: 0,
    label: 'No DR',
    confidence: 0,
    class_name: 'No DR'
  };
  const referable = result.referable || {
    probability: 0,
    threshold: 0.13,
    status: 'NON_REFERABLE',
    is_referable: false
  };
  const isReferable = referable.status === 'REFERABLE' || referable.is_referable;
  const style = getSeverityStyle(prediction.class_id);
  const quality = result.quality;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-7 border border-surface-700/80 shadow-2xl">
      <div className="flex items-center justify-between pb-4 border-b border-surface-800">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-surface-800 text-surface-200 border border-surface-700">
            <FileText className="w-5 h-5 text-brand-400" />
          </div>
          <div>
            <h3 className="text-base sm:text-lg font-bold text-surface-100">
              Screening Telemetry & Audit Record
            </h3>
            <p className="text-xs text-surface-400">
              Audit ID: <span className="font-mono text-brand-400">{result.screening_id || result.id}</span>
            </p>
          </div>
        </div>

        <button
          onClick={handlePrint}
          className="px-3.5 py-1.5 rounded-xl bg-surface-900 hover:bg-surface-800 text-surface-200 border border-surface-700 text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-sm"
        >
          <Printer className="w-4 h-4 text-surface-400" />
          <span>Print / Export</span>
        </button>
      </div>

      {/* Summary Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3.5 mt-5 text-xs">
        <div className="p-3.5 rounded-xl bg-surface-950/70 border border-surface-800/80">
          <span className="text-surface-400 block mb-1">DR Severity Grade</span>
          <span className={`font-bold font-mono text-sm ${style.text}`}>
            {prediction.label || prediction.class_name} (Grade {prediction.class_id})
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-surface-950/70 border border-surface-800/80">
          <span className="text-surface-400 block mb-1">Grade Confidence</span>
          <span className="font-bold font-mono text-sm text-surface-100">
            {formatPercent(prediction.confidence, 2)}
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-surface-950/70 border border-surface-800/80">
          <span className="text-surface-400 block mb-1">Referable Status</span>
          <span className={`font-bold text-sm ${isReferable ? 'text-rose-400' : 'text-emerald-400'}`}>
            {isReferable ? 'REFERABLE (Positive)' : 'NON-REFERABLE (Negative)'}
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-surface-950/70 border border-surface-800/80">
          <span className="text-surface-400 block mb-1">Referable Probability</span>
          <span className="font-bold font-mono text-sm text-surface-100">
            {formatPercent(referable.probability, 2)}
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-surface-950/70 border border-surface-800/80">
          <span className="text-surface-400 block mb-1">Operating Threshold</span>
          <span className="font-bold font-mono text-sm text-amber-400">
            {referable.threshold}
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-surface-950/70 border border-surface-800/80">
          <span className="text-surface-400 block mb-1">Quality Gate</span>
          <span className="font-bold font-mono text-sm text-emerald-400 flex items-center space-x-1">
            <Check className="w-3.5 h-3.5 inline" />
            <span>{quality?.status || 'ACCEPT'}</span>
          </span>
        </div>
      </div>

      {/* Metadata Footer */}
      <div className="mt-5 pt-4 border-t border-surface-800/80 flex flex-col sm:flex-row items-start sm:items-center justify-between text-[11px] text-surface-400 gap-2 font-mono">
        <div className="flex items-center space-x-1.5">
          <Clock className="w-3.5 h-3.5 text-surface-500" />
          <span>Timestamp: {result.created_at || (result.timestamp ? String(result.timestamp) : new Date().toISOString())}</span>
        </div>
        <div>
          <span>Model: {result.model?.name || 'EfficientNet-B3'} ({result.model?.version || 'b3-aptos-epoch7'})</span>
        </div>
        <div className="truncate max-w-xs">
          <span>File: {result.filename || 'retinal_image.jpg'}</span>
        </div>
      </div>
    </div>
  );
};
