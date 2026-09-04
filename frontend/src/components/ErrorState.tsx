import React from 'react';
import { AlertTriangle, RefreshCw, ShieldAlert, CameraOff, FileX, Info } from 'lucide-react';

export interface ErrorStateProps {
  status?: 'INVALID_FILE' | 'INVALID_IMAGE' | 'LOW_QUALITY' | 'API_ERROR';
  message: string;
  reasons?: string[];
  screeningId?: string;
  onRetry: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  status = 'API_ERROR',
  message,
  reasons = [],
  screeningId,
  onRetry,
}) => {
  const getHeader = () => {
    switch (status) {
      case 'INVALID_IMAGE':
        return {
          title: 'Non-Retinal Image Detected',
          subtitle: 'The safety gate determined this image is not a retinal fundus photograph.',
          color: 'border-amber-500/40 bg-amber-950/20 text-amber-400',
          badgeBg: 'bg-amber-500/20 border-amber-500/30 text-amber-400',
          icon: <ShieldAlert className="w-8 h-8" />,
          actionable: 'Please provide an authentic digital fundus photograph with circular field-of-view aperture.',
        };
      case 'LOW_QUALITY':
        return {
          title: 'Image Quality Insufficient',
          subtitle: 'Automated screening was safely halted to prevent inaccurate or misleading DR predictions.',
          color: 'border-orange-500/40 bg-orange-950/20 text-orange-400',
          badgeBg: 'bg-orange-500/20 border-orange-500/30 text-orange-400',
          icon: <CameraOff className="w-8 h-8" />,
          actionable: 'Please capture a well-focused, evenly illuminated fundus photograph and re-upload.',
        };
      case 'INVALID_FILE':
        return {
          title: 'Invalid File Upload',
          subtitle: 'The submitted file did not pass file integrity or format validation.',
          color: 'border-rose-500/40 bg-rose-950/20 text-rose-400',
          badgeBg: 'bg-rose-500/20 border-rose-500/30 text-rose-400',
          icon: <FileX className="w-8 h-8" />,
          actionable: 'Ensure you upload a JPEG or PNG image under 10 MB in size.',
        };
      default:
        return {
          title: 'Analysis Interrupted',
          subtitle: 'An unexpected connection or backend server error occurred.',
          color: 'border-rose-500/40 bg-rose-950/20 text-rose-400',
          badgeBg: 'bg-rose-500/20 border-rose-500/30 text-rose-400',
          icon: <AlertTriangle className="w-8 h-8" />,
          actionable: 'Verify backend API connectivity and try again.',
        };
    }
  };

  const header = getHeader();

  return (
    <div className={`glass-panel rounded-2xl p-6 sm:p-10 shadow-2xl border text-center max-w-lg mx-auto ${header.color}`}>
      <div className={`w-16 h-16 rounded-2xl border flex items-center justify-center mx-auto mb-5 shadow-lg ${header.badgeBg}`}>
        {header.icon}
      </div>

      <div className="inline-block px-3 py-1 rounded-full text-xs font-semibold tracking-wider uppercase mb-3 bg-surface-900/60 border border-surface-700 text-surface-300">
        Status: {status}
      </div>

      <h3 className="text-xl font-bold text-surface-100 mb-2">
        {header.title}
      </h3>
      
      <p className="text-xs sm:text-sm text-surface-300 mb-4 leading-relaxed">
        {message || header.subtitle}
      </p>

      {reasons && reasons.length > 0 && (
        <div className="bg-surface-950/70 rounded-xl p-4 mb-5 text-left border border-surface-800">
          <div className="flex items-center space-x-2 text-xs font-semibold text-surface-300 mb-2">
            <Info className="w-3.5 h-3.5 text-brand-400" />
            <span>Validation Gate Findings:</span>
          </div>
          <ul className="space-y-1.5 text-xs text-surface-400 list-disc list-inside">
            {reasons.map((r, idx) => (
              <li key={idx} className="leading-snug">{r}</li>
            ))}
          </ul>
        </div>
      )}

      <p className="text-xs text-surface-400 mb-6 italic">
        {header.actionable}
      </p>

      {screeningId && (
        <p className="text-[11px] font-mono text-surface-500 mb-5">
          Audit ID: {screeningId}
        </p>
      )}

      <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
        <button
          onClick={onRetry}
          className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-gradient-to-r from-brand-600 to-emerald-500 hover:from-brand-500 hover:to-emerald-400 text-white text-xs sm:text-sm font-semibold shadow-glow-emerald flex items-center justify-center space-x-2 transition-all"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Upload Another Image</span>
        </button>
      </div>
    </div>
  );
};
