import React from 'react';
import { BarChart3, Info } from 'lucide-react';
import { ProbabilitiesDict } from '../types/prediction';
import { getSeverityStyle, formatPercent } from '../utils/formatting';

interface ProbabilityChartProps {
  probabilities: ProbabilitiesDict;
  predictedClassId: number;
}

const CLASS_ORDER = [
  { id: 0, name: 'No DR' },
  { id: 1, name: 'Mild DR' },
  { id: 2, name: 'Moderate DR' },
  { id: 3, name: 'Severe DR' },
  { id: 4, name: 'Proliferative DR' },
];

export const ProbabilityChart: React.FC<ProbabilityChartProps> = ({
  probabilities,
  predictedClassId,
}) => {
  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-7 border border-surface-700/80 shadow-2xl">
      <div className="flex items-center justify-between pb-4 border-b border-surface-800">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-medblue-500/10 text-medblue-400 border border-medblue-500/20">
            <BarChart3 className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base sm:text-lg font-bold text-surface-100">
              5-Class Severity Probability Distribution
            </h3>
            <p className="text-xs text-surface-400">
              Multi-class softmax distribution across diabetic retinopathy stages
            </p>
          </div>
        </div>
      </div>

      {/* Horizontal Bar Breakdown */}
      <div className="mt-6 space-y-4">
        {CLASS_ORDER.map((item) => {
          const prob = probabilities[item.name] ?? 0;
          const isPredicted = item.id === predictedClassId;
          const style = getSeverityStyle(item.id);

          return (
            <div
              key={item.id}
              className={`p-3 rounded-xl transition-all duration-200 border ${
                isPredicted
                  ? 'bg-surface-800/80 border-surface-600 shadow-md'
                  : 'bg-surface-950/40 border-transparent hover:border-surface-800'
              }`}
            >
              <div className="flex items-center justify-between text-xs sm:text-sm mb-1.5">
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-surface-400 text-xs">[{item.id}]</span>
                  <span className={`font-semibold ${isPredicted ? 'text-surface-100 font-bold' : 'text-surface-300'}`}>
                    {item.name}
                  </span>
                  {isPredicted && (
                    <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${style.badge}`}>
                      Top Prediction
                    </span>
                  )}
                </div>

                <div className="flex items-center space-x-2 font-mono">
                  <span className={`text-xs sm:text-sm font-bold ${isPredicted ? style.text : 'text-surface-300'}`}>
                    {formatPercent(prob, 2)}
                  </span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-2.5 bg-surface-950 rounded-full overflow-hidden p-0.5 border border-surface-800/80">
                <div
                  className="h-full rounded-full transition-all duration-1000 ease-out"
                  style={{
                    width: `${Math.max(prob * 100, 1.5)}%`,
                    backgroundColor: style.color,
                    opacity: isPredicted ? 1.0 : 0.65,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-5 pt-3 border-t border-surface-800/60 flex items-center space-x-2 text-[11px] text-surface-400">
        <Info className="w-3.5 h-3.5 text-surface-400 shrink-0" />
        <span>Probabilities reflect raw neural network softmax outputs and sum to 100%.</span>
      </div>
    </div>
  );
};
