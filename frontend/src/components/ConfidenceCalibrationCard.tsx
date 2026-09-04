import React from 'react';
import { Gauge, Sparkles, Scale, Info } from 'lucide-react';
import { CalibrationInfo } from '../types/prediction';

interface ConfidenceCalibrationCardProps {
  calibration?: CalibrationInfo;
  rawConfidence: number;
}

export const ConfidenceCalibrationCard: React.FC<ConfidenceCalibrationCardProps> = ({ calibration, rawConfidence }) => {
  if (!calibration || !calibration.is_calibrated) {
    return null;
  }

  const temp = calibration.temperature;
  const calConf = Math.round(calibration.calibrated_confidence * 100);
  const rawConf = Math.round(rawConfidence * 100);
  const eceReduction = calibration.metrics?.ece_reduction_percent;

  return (
    <div className="card-glass border border-surface-800/80 rounded-2xl p-6 shadow-xl space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-surface-800">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-violet-950/60 border border-violet-800/80 text-violet-400">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-surface-100 flex items-center gap-2">
              Post-Hoc Confidence Calibration
              <span className="text-xs px-2 py-0.5 rounded-full bg-violet-950 text-violet-300 border border-violet-800/60 font-mono">Phase 7</span>
            </h3>
            <p className="text-xs text-surface-400">Temperature scaling mitigation of modern deep network overconfidence</p>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-xs font-mono font-semibold bg-violet-950/40 text-violet-300 border border-violet-800/60 px-3 py-1.5 rounded-lg">
          <Gauge className="w-3.5 h-3.5" />
          <span>Temperature T = {temp.toFixed(2)}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Calibrated Confidence Box */}
        <div className="p-4 rounded-xl bg-violet-950/30 border border-violet-800/60 space-y-2">
          <div className="flex justify-between items-center text-xs">
            <span className="text-violet-300 font-semibold flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-violet-400" />
              Calibrated Top-1 Confidence
            </span>
            <span className="text-lg font-extrabold text-violet-200 font-mono">{calConf}%</span>
          </div>
          <div className="w-full bg-surface-900 rounded-full h-2.5 overflow-hidden">
            <div
              className="bg-gradient-to-r from-violet-500 to-indigo-400 h-full rounded-full transition-all duration-700"
              style={{ width: `${calConf}%` }}
            />
          </div>
          <div className="text-[11px] text-surface-400">
            Temperature-scaled probability: softens peak overconfidence without altering predicted grade.
          </div>
        </div>

        {/* Raw Confidence Box */}
        <div className="p-4 rounded-xl bg-surface-900/60 border border-surface-800/80 space-y-2">
          <div className="flex justify-between items-center text-xs">
            <span className="text-surface-300 font-semibold">Raw Uncalibrated Softmax</span>
            <span className="text-lg font-extrabold text-surface-300 font-mono">{rawConf}%</span>
          </div>
          <div className="w-full bg-surface-900 rounded-full h-2.5 overflow-hidden">
            <div
              className="bg-surface-600 h-full rounded-full transition-all duration-700"
              style={{ width: `${rawConf}%` }}
            />
          </div>
          <div className="text-[11px] text-surface-400">
            Raw output directly from EfficientNet-B3 classifier head prior to calibration.
          </div>
        </div>
      </div>

      {eceReduction !== undefined && eceReduction > 0 && (
        <div className="p-3 rounded-xl bg-surface-900/80 border border-surface-800 text-xs text-surface-400 flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-violet-400 shrink-0" />
            Expected Calibration Error (ECE) Improvement:
          </span>
          <span className="font-mono font-bold text-emerald-400">+{eceReduction.toFixed(1)}% Reliability</span>
        </div>
      )}
    </div>
  );
};
