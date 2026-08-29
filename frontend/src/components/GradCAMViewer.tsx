import React, { useState } from 'react';
import { Layers, Eye, Sparkles, Sliders, Info, Maximize2, Download } from 'lucide-react';
import { ExplainabilityInfo } from '../types/prediction';

interface GradCAMViewerProps {
  explainability: ExplainabilityInfo;
  classNameTitle: string;
}

type TabType = 'overlay' | 'heatmap' | 'original' | 'split';

export const GradCAMViewer: React.FC<GradCAMViewerProps> = ({
  explainability,
  classNameTitle,
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('overlay');
  const [overlayAlpha, setOverlayAlpha] = useState<number>(0.45);

  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-7 border border-surface-700/80 shadow-2xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-surface-800">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-gradient-to-tr from-brand-500/20 to-medblue-500/20 text-brand-400 border border-brand-500/30">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-base sm:text-lg font-bold text-surface-100">
                Grad-CAM Visual Explainability
              </h3>
              <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-brand-500/10 text-brand-400 border border-brand-500/20">
                features[-1]
              </span>
            </div>
            <p className="text-xs text-surface-400">
              Visual attention heatmap computed from convolutional feature activations for <span className="text-brand-300 font-semibold">{classNameTitle}</span>
            </p>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center p-1 bg-surface-950 rounded-xl border border-surface-800 self-start sm:self-auto overflow-x-auto max-w-full">
          <button
            onClick={() => setActiveTab('overlay')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
              activeTab === 'overlay'
                ? 'bg-brand-500/20 text-brand-300 border border-brand-500/40 shadow-sm'
                : 'text-surface-400 hover:text-surface-200'
            }`}
          >
            Overlay Blend
          </button>
          <button
            onClick={() => setActiveTab('heatmap')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
              activeTab === 'heatmap'
                ? 'bg-brand-500/20 text-brand-300 border border-brand-500/40 shadow-sm'
                : 'text-surface-400 hover:text-surface-200'
            }`}
          >
            Attention Heatmap
          </button>
          <button
            onClick={() => setActiveTab('original')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
              activeTab === 'original'
                ? 'bg-brand-500/20 text-brand-300 border border-brand-500/40 shadow-sm'
                : 'text-surface-400 hover:text-surface-200'
            }`}
          >
            Original Fundus
          </button>
          <button
            onClick={() => setActiveTab('split')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
              activeTab === 'split'
                ? 'bg-brand-500/20 text-brand-300 border border-brand-500/40 shadow-sm'
                : 'text-surface-400 hover:text-surface-200'
            }`}
          >
            Side-by-Side
          </button>
        </div>
      </div>

      {/* Main Visual Display */}
      <div className="mt-6">
        {activeTab === 'split' ? (
          /* Side-by-Side View */
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* 1. Original */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs text-surface-400 px-1 font-semibold">
                <span>1. Original Preprocessed</span>
                <span className="font-mono text-[10px]">380×380</span>
              </div>
              <div className="relative aspect-square rounded-xl overflow-hidden bg-black border border-surface-800 shadow-lg">
                <img
                  src={explainability.original_url}
                  alt="Original Preprocessed Retinal Fundus"
                  className="w-full h-full object-contain"
                />
              </div>
            </div>

            {/* 2. Heatmap */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs text-surface-400 px-1 font-semibold">
                <span>2. Grad-CAM Activation</span>
                <span className="font-mono text-[10px]">JET Colormap</span>
              </div>
              <div className="relative aspect-square rounded-xl overflow-hidden bg-black border border-surface-800 shadow-lg">
                <img
                  src={explainability.heatmap_url}
                  alt="Grad-CAM Heatmap"
                  className="w-full h-full object-contain"
                />
              </div>
            </div>

            {/* 3. Overlay */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs text-brand-400 px-1 font-semibold">
                <span>3. Explanation Overlay</span>
                <span className="font-mono text-[10px]">Composite</span>
              </div>
              <div className="relative aspect-square rounded-xl overflow-hidden bg-black border border-brand-500/30 shadow-glow-emerald">
                <img
                  src={explainability.overlay_url}
                  alt="Grad-CAM Overlay"
                  className="w-full h-full object-contain"
                />
              </div>
            </div>
          </div>
        ) : (
          /* Single Tab View with interactive blend */
          <div className="flex flex-col items-center">
            <div className="relative w-full max-w-md aspect-square rounded-2xl overflow-hidden bg-black border-2 border-surface-700 shadow-2xl flex items-center justify-center">
              {activeTab === 'original' && (
                <img
                  src={explainability.original_url}
                  alt="Original Preprocessed Fundus"
                  className="w-full h-full object-contain animate-in fade-in duration-200"
                />
              )}
              {activeTab === 'heatmap' && (
                <img
                  src={explainability.heatmap_url}
                  alt="Grad-CAM Activation Heatmap"
                  className="w-full h-full object-contain animate-in fade-in duration-200"
                />
              )}
              {activeTab === 'overlay' && (
                <div className="relative w-full h-full flex items-center justify-center">
                  <img
                    src={explainability.overlay_url}
                    alt="Grad-CAM Overlay Composite"
                    className="w-full h-full object-contain animate-in fade-in duration-200"
                  />
                </div>
              )}
            </div>

            {/* Colormap Legend */}
            <div className="w-full max-w-md mt-4 p-3 bg-surface-950/80 rounded-xl border border-surface-800 flex items-center justify-between text-xs">
              <span className="text-surface-400 font-medium">Attention Intensity:</span>
              <div className="flex items-center space-x-2">
                <span className="text-[11px] font-mono text-blue-400">Low (0.0)</span>
                <div className="w-28 h-3 rounded-full bg-gradient-to-r from-blue-600 via-emerald-400 via-amber-400 to-rose-600 border border-white/20" />
                <span className="text-[11px] font-mono text-rose-400">High (1.0)</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Scientific Explanation Caption */}
      <div className="mt-6 p-4 rounded-xl bg-surface-950/70 border border-surface-800 text-xs text-surface-300 leading-relaxed flex items-start space-x-2.5">
        <Info className="w-4 h-4 text-brand-400 shrink-0 mt-0.5" />
        <p>
          <strong>Explainability Interpretation:</strong> Highlighted regions indicate image areas that contributed more strongly to the model's prediction. This visualization is an AI explanation and should not be interpreted as a clinical lesion segmentation.
        </p>
      </div>
    </div>
  );
};
