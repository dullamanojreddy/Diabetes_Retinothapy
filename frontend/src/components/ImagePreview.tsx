import React from 'react';
import { Eye, Trash2, ArrowRight, FileText, CheckCircle2 } from 'lucide-react';
import { formatFileSize } from '../utils/formatting';

interface ImagePreviewProps {
  file: File;
  previewUrl: string;
  onRemove: () => void;
  onAnalyze: () => void;
  disabled?: boolean;
}

export const ImagePreview: React.FC<ImagePreviewProps> = ({
  file,
  previewUrl,
  onRemove,
  onAnalyze,
  disabled = false,
}) => {
  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-8 shadow-2xl border border-surface-700/60 animate-in fade-in zoom-in-95 duration-200">
      <div className="flex flex-col lg:flex-row items-center gap-8">
        {/* Retinal Image Frame */}
        <div className="relative group w-64 h-64 sm:w-80 sm:h-80 rounded-2xl overflow-hidden bg-black/80 border-2 border-surface-700/80 shadow-2xl flex items-center justify-center shrink-0">
          <img
            src={previewUrl}
            alt="Retinal Fundus Preview"
            className="w-full h-full object-contain transform group-hover:scale-105 transition-transform duration-300"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-surface-950/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end justify-center p-3 pointer-events-none">
            <span className="text-[11px] font-mono text-brand-300 bg-surface-950/80 px-2.5 py-1 rounded-full border border-brand-500/30">
              Retinal Fundus View
            </span>
          </div>
        </div>

        {/* Details & Actions */}
        <div className="flex-1 w-full space-y-6">
          <div>
            <div className="flex items-center space-x-2 text-xs font-semibold text-brand-400 uppercase tracking-wider">
              <CheckCircle2 className="w-4 h-4" />
              <span>Image Validated & Ready</span>
            </div>
            <h3 className="text-xl sm:text-2xl font-bold text-surface-100 mt-1 truncate" title={file.name}>
              {file.name}
            </h3>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-surface-900/80 p-3 rounded-xl border border-surface-800">
              <span className="text-surface-400 block">File Size</span>
              <span className="font-semibold text-surface-200 mt-0.5 block font-mono">
                {formatFileSize(file.size)}
              </span>
            </div>
            <div className="bg-surface-900/80 p-3 rounded-xl border border-surface-800">
              <span className="text-surface-400 block">MIME Type</span>
              <span className="font-semibold text-surface-200 mt-0.5 block font-mono uppercase">
                {file.type || 'image/jpeg'}
              </span>
            </div>
            <div className="bg-surface-900/80 p-3 rounded-xl border border-surface-800">
              <span className="text-surface-400 block">Target Resolution</span>
              <span className="font-semibold text-surface-200 mt-0.5 block font-mono">
                380 × 380 (EfficientNet-B3)
              </span>
            </div>
            <div className="bg-surface-900/80 p-3 rounded-xl border border-surface-800">
              <span className="text-surface-400 block">Explainability</span>
              <span className="font-semibold text-brand-400 mt-0.5 block">
                Grad-CAM Enabled
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
            <button
              onClick={onAnalyze}
              disabled={disabled}
              className="w-full sm:flex-1 py-3.5 px-6 rounded-xl bg-gradient-to-r from-brand-600 via-brand-500 to-emerald-500 hover:from-brand-500 hover:to-emerald-400 text-white font-semibold text-sm shadow-glow-emerald flex items-center justify-center space-x-2 transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none"
            >
              <Eye className="w-5 h-5" />
              <span>Run AI Screening Analysis</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </button>

            <button
              onClick={onRemove}
              disabled={disabled}
              className="w-full sm:w-auto py-3.5 px-4 rounded-xl bg-surface-900 hover:bg-surface-800 text-surface-400 hover:text-rose-400 border border-surface-800 hover:border-rose-500/40 text-sm font-medium transition-all flex items-center justify-center space-x-2"
              title="Remove image"
            >
              <Trash2 className="w-4 h-4" />
              <span className="sm:hidden">Remove</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
