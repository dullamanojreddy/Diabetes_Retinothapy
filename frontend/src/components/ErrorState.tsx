import React from 'react';
import { AlertTriangle, RefreshCw, ArrowLeft } from 'lucide-react';

interface ErrorStateProps {
  message: string;
  onRetry: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ message, onRetry }) => {
  return (
    <div className="glass-panel rounded-2xl p-8 sm:p-12 shadow-2xl border border-rose-500/40 text-center max-w-lg mx-auto bg-rose-950/20">
      <div className="w-16 h-16 rounded-2xl bg-rose-500/20 border border-rose-500/30 text-rose-400 flex items-center justify-center mx-auto mb-6 shadow-glow-red">
        <AlertTriangle className="w-8 h-8" />
      </div>

      <h3 className="text-xl font-bold text-surface-100 mb-2">
        Analysis Interrupted
      </h3>
      <p className="text-xs sm:text-sm text-surface-300 mb-6 leading-relaxed">
        {message || 'An unexpected error occurred while communicating with the AI screening backend.'}
      </p>

      <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
        <button
          onClick={onRetry}
          className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-gradient-to-r from-brand-600 to-emerald-500 hover:from-brand-500 hover:to-emerald-400 text-white text-xs sm:text-sm font-semibold shadow-glow-emerald flex items-center justify-center space-x-2 transition-all"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Try Again</span>
        </button>
      </div>
    </div>
  );
};
