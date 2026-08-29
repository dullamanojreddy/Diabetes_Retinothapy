import React from 'react';
import { AlertOctagon, CheckCircle2, ArrowUpRight, Activity, Info } from 'lucide-react';
import { ReferableRiskInfo } from '../types/prediction';
import { formatPercent } from '../utils/formatting';

interface ReferableRiskProps {
  referable: ReferableRiskInfo;
  recommendationText: string;
}

export const ReferableRisk: React.FC<ReferableRiskProps> = ({
  referable,
  recommendationText,
}) => {
  const isReferable = referable.is_referable;

  return (
    <div className={`rounded-2xl p-6 sm:p-7 border ${
      isReferable
        ? 'bg-rose-950/40 border-rose-500/40 shadow-glow-red'
        : 'bg-emerald-950/40 border-emerald-500/40 shadow-glow-emerald'
    } shadow-2xl backdrop-blur-md transition-all duration-300`}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/10">
        <div className="flex items-center space-x-3">
          <div className={`p-2.5 rounded-xl ${
            isReferable ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
          }`}>
            {isReferable ? <AlertOctagon className="w-6 h-6" /> : <CheckCircle2 className="w-6 h-6" />}
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-surface-400 block">
              Referable DR Assessment (Grades 1–4)
            </span>
            <div className="flex items-center space-x-2 mt-0.5">
              <span className={`text-xl sm:text-2xl font-black tracking-tight ${
                isReferable ? 'text-rose-300' : 'text-emerald-300'
              }`}>
                {isReferable ? 'REFERABLE DR (POSITIVE)' : 'NON-REFERABLE DR (NEGATIVE)'}
              </span>
            </div>
          </div>
        </div>

        {/* Risk Probability Pill */}
        <div className="bg-surface-950/80 px-4 py-2 rounded-xl border border-white/10 flex flex-col items-end">
          <span className="text-[10px] text-surface-400 font-semibold uppercase">Referable Probability</span>
          <span className={`text-lg font-mono font-bold ${isReferable ? 'text-rose-400' : 'text-emerald-400'}`}>
            {formatPercent(referable.probability, 2)}
          </span>
        </div>
      </div>

      {/* Threshold Comparison Bar */}
      <div className="mt-4 space-y-3">
        <div>
          <div className="flex justify-between text-xs text-surface-300 mb-1 font-mono">
            <span>Operating Threshold: {formatPercent(referable.threshold, 0)}</span>
            <span>Calculated Score: {formatPercent(referable.probability, 1)}</span>
          </div>

          <div className="relative w-full h-3 bg-surface-950 rounded-full overflow-hidden border border-white/10">
            {/* Threshold Line */}
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-amber-400 z-10"
              style={{ left: `${referable.threshold * 100}%` }}
              title={`Cutoff Threshold: ${referable.threshold}`}
            />
            {/* Probability Fill */}
            <div
              className={`h-full rounded-full transition-all duration-1000 ${
                isReferable ? 'bg-gradient-to-r from-amber-500 to-rose-500' : 'bg-gradient-to-r from-emerald-600 to-emerald-400'
              }`}
              style={{ width: `${Math.min(Math.max(referable.probability * 100, 2), 100)}%` }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-surface-400 mt-1 font-mono">
            <span>0% (Low Risk)</span>
            <span className="text-amber-400 font-semibold">▲ Threshold ({referable.threshold})</span>
            <span>100% (High Risk)</span>
          </div>
        </div>

        {/* Referral Action Advisory */}
        <div className="bg-surface-950/70 rounded-xl p-3.5 border border-white/10 text-xs sm:text-sm text-surface-300 leading-relaxed">
          <div className="flex items-start space-x-2">
            <Activity className="w-4 h-4 text-brand-400 shrink-0 mt-0.5" />
            <span>{recommendationText}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
