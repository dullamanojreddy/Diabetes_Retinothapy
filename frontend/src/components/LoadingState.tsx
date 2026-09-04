import React, { useState, useEffect } from 'react';
import { Eye, Cpu, Layers, Sparkles, CheckCircle2, Loader2 } from 'lucide-react';

const STAGES = [
  { id: 1, text: 'Validating retinal fundus format & dimensions...', icon: Eye },
  { id: 2, text: 'Cropping retinal field-of-view & normalizing to 380×380...', icon: Layers },
  { id: 3, text: 'Evaluating EfficientNet-B3 5-class neural network...', icon: Cpu },
  { id: 4, text: 'Computing gradient activations & Grad-CAM heatmap...', icon: Sparkles },
  { id: 5, text: 'Synthesizing referable risk & clinical recommendations...', icon: CheckCircle2 },
];

export const LoadingState: React.FC = () => {
  const [currentStage, setCurrentStage] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStage((prev) => (prev < STAGES.length - 1 ? prev + 1 : prev));
    }, 900);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="glass-panel rounded-2xl p-8 sm:p-12 shadow-2xl border border-surface-700/80 text-center max-w-xl mx-auto">
      {/* Animated Glowing Fundus Scanner Graphic */}
      <div className="relative w-32 h-32 mx-auto mb-8">
        <div className="w-full h-full rounded-full bg-gradient-to-tr from-brand-500/20 via-medblue-500/20 to-brand-400/20 border-2 border-brand-500/40 flex items-center justify-center p-2 shadow-glow-emerald">
          <div className="w-full h-full rounded-full bg-surface-950/90 flex items-center justify-center relative overflow-hidden">
            <Eye className="w-12 h-12 text-brand-400 animate-pulse" />
            {/* Moving Laser Scanner Line */}
            <div className="absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-brand-400 to-transparent shadow-[0_0_12px_#34d399] animate-scanline" />
          </div>
        </div>
        <div className="absolute -inset-2 rounded-full border border-brand-400/20 animate-ping opacity-25 pointer-events-none" />
      </div>

      <h3 className="text-xl sm:text-2xl font-bold text-surface-100 mb-2">
        Analyzing Retinal Fundus
      </h3>
      <p className="text-xs sm:text-sm text-surface-400 mb-8">
        Running deterministic inference through EfficientNet-B3 and generating explainability maps.
      </p>

      {/* Progressive Stage Checklist */}
      <div className="space-y-3 text-left max-w-md mx-auto">
        {STAGES.map((stage, idx) => {
          const isPast = idx < currentStage;
          const isCurrent = idx === currentStage;

          return (
            <div
              key={stage.id}
              className={`flex items-center space-x-3 p-2.5 rounded-xl border transition-all duration-300 ${
                isCurrent
                  ? 'bg-brand-950/40 border-brand-500/40 text-brand-200 shadow-sm'
                  : isPast
                  ? 'bg-surface-900/40 border-surface-800 text-surface-400'
                  : 'bg-transparent border-transparent text-surface-400 opacity-40'
              }`}
            >
              <div className="shrink-0">
                {isPast ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : isCurrent ? (
                  <Loader2 className="w-4 h-4 text-brand-400 animate-spin" />
                ) : (
                  <div className="w-4 h-4 rounded-full border border-surface-700" />
                )}
              </div>
              <span className="text-xs sm:text-sm font-medium leading-tight">
                {stage.text}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
