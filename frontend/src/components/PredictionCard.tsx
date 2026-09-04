import React from 'react';
import { Shield, Sparkles, HelpCircle, CheckCircle, AlertTriangle } from 'lucide-react';
import { PredictionClassInfo } from '../types/prediction';
import { getSeverityStyle, formatPercent } from '../utils/formatting';

interface PredictionCardProps {
  prediction: PredictionClassInfo;
  explanationText: string;
}

export const PredictionCard: React.FC<PredictionCardProps> = ({
  prediction,
  explanationText,
}) => {
  const style = getSeverityStyle(prediction.class_id);
  const displayName = prediction.label || prediction.class_name || `Class ${prediction.class_id}`;

  return (
    <div className={`rounded-2xl p-6 sm:p-7 border ${style.border} ${style.bg} ${style.glow} shadow-2xl backdrop-blur-md relative overflow-hidden transition-all duration-300`}>
      {/* Background Accent Glow */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-white/10">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-surface-400">
            <span>Primary AI Classification</span>
            <span>•</span>
            <span className="font-mono">Grade {prediction.class_id} of 4</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white mt-1 tracking-tight">
            {displayName}
          </h2>
        </div>

        {/* Severity Badge */}
        <div className={`px-4 py-2 rounded-xl ${style.badge} font-bold text-sm tracking-wide self-start sm:self-auto flex items-center space-x-2 shadow-sm`}>
          <span className="w-2.5 h-2.5 rounded-full bg-current animate-pulse" />
          <span>DR Grade {prediction.class_id}</span>
        </div>
      </div>

      {/* Confidence & Rationale Section */}
      <div className="mt-5 space-y-4">
        <div>
          <div className="flex justify-between items-center text-xs font-semibold mb-1.5">
            <span className="text-surface-300">Classification Confidence</span>
            <span className="text-surface-100 font-mono text-sm">
              {formatPercent(prediction.confidence, 2)}
            </span>
          </div>
          {/* Visual Progress Bar */}
          <div className="w-full h-3 bg-surface-950/80 rounded-full overflow-hidden p-0.5 border border-white/10">
            <div
              className="h-full rounded-full transition-all duration-1000 ease-out shadow-sm"
              style={{
                width: `${Math.max(prediction.confidence * 100, 3)}%`,
                backgroundColor: style.color
              }}
            />
          </div>
        </div>

        {/* Clinical Rationale Text */}
        <div className="bg-surface-950/60 rounded-xl p-4 border border-white/10">
          <div className="flex items-start space-x-2.5">
            <Sparkles className="w-4 h-4 text-brand-400 shrink-0 mt-0.5" />
            <div>
              <span className="text-xs font-semibold text-surface-300 block mb-0.5">
                Screening Indication Rationale
              </span>
              <p className="text-xs sm:text-sm text-surface-300 leading-relaxed">
                {explanationText}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
