import React from 'react';
import {
  Eye,
  Activity,
  Sparkles,
  ShieldCheck,
  ArrowRight,
  CheckCircle2,
  Cpu,
  Layers,
  ChevronRight,
  Database,
  BarChart2,
  FileCheck
} from 'lucide-react';
import { MedicalDisclaimer } from '../components/MedicalDisclaimer';

interface HomeProps {
  onStartScreening: () => void;
}

export const Home: React.FC<HomeProps> = ({ onStartScreening }) => {
  return (
    <div className="space-y-16 py-6 sm:py-10">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-3xl border border-surface-800 bg-gradient-to-b from-surface-900/90 via-surface-950/80 to-surface-950 p-8 sm:p-14 lg:p-16 shadow-2xl backdrop-blur-xl">
        {/* Background ambient lighting */}
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-medblue-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-300 text-xs font-semibold uppercase tracking-wider mb-6">
            <Sparkles className="w-3.5 h-3.5" />
            <span>EfficientNet-B3 Deep Learning • Grad-CAM Explainability</span>
          </div>

          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold text-surface-100 tracking-tight leading-[1.15]">
            Explainable Diabetic Retinopathy{' '}
            <span className="bg-gradient-to-r from-brand-400 via-emerald-300 to-medblue-400 bg-clip-text text-transparent">
              Screening
            </span>
          </h1>

          <p className="mt-5 text-base sm:text-xl text-surface-300 font-normal leading-relaxed">
            AI-assisted retinal image screening with transparent visual explanations. Classify DR severity across 5 standardized clinical grades and evaluate referable risk in seconds.
          </p>

          {/* Action CTAs */}
          <div className="mt-8 flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
            <button
              onClick={onStartScreening}
              className="py-4 px-8 rounded-xl bg-gradient-to-r from-brand-600 via-brand-500 to-emerald-500 hover:from-brand-500 hover:to-emerald-400 text-white font-bold text-sm sm:text-base shadow-glow-emerald flex items-center justify-center space-x-3 transition-all duration-200 hover:scale-105 active:scale-95"
            >
              <Eye className="w-5 h-5" />
              <span>Start Screening Now</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </button>

            <a
              href="#benchmarks"
              className="py-4 px-6 rounded-xl bg-surface-900 hover:bg-surface-800 text-surface-300 hover:text-surface-100 border border-surface-700 text-sm font-semibold flex items-center justify-center space-x-2 transition-colors"
            >
              <span>View Model Benchmarks</span>
              <ChevronRight className="w-4 h-4" />
            </a>
          </div>

          {/* Quick trust metrics */}
          <div className="mt-10 pt-8 border-t border-surface-800/80 grid grid-cols-3 gap-4 text-left">
            <div>
              <div className="text-xl sm:text-2xl font-black font-mono text-brand-300">0.9827</div>
              <div className="text-[11px] text-surface-400 uppercase tracking-wider font-semibold">Referable ROC-AUC</div>
            </div>
            <div>
              <div className="text-xl sm:text-2xl font-black font-mono text-emerald-300">85.40%</div>
              <div className="text-[11px] text-surface-400 uppercase tracking-wider font-semibold">Sensitivity</div>
            </div>
            <div>
              <div className="text-xl sm:text-2xl font-black font-mono text-medblue-300">96.07%</div>
              <div className="text-[11px] text-surface-400 uppercase tracking-wider font-semibold">Specificity</div>
            </div>
          </div>
        </div>
      </section>

      {/* 3 Core Pillars */}
      <section className="space-y-6">
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-surface-100">
            End-to-End Explainable Screening Pipeline
          </h2>
          <p className="text-xs sm:text-sm text-surface-400 mt-2">
            Engineered to empower researchers and clinicians with transparent, reproducible, and verifiable model outputs.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Pillar 1 */}
          <div className="glass-panel glass-panel-hover rounded-2xl p-7 border border-surface-700/60 shadow-xl space-y-4">
            <div className="w-12 h-12 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-400 flex items-center justify-center">
              <Eye className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-surface-100">
              5-Class Severity Classification
            </h3>
            <p className="text-xs sm:text-sm text-surface-400 leading-relaxed">
              Standardized ICDR grading: No DR (0), Mild (1), Moderate (2), Severe (3), and Proliferative DR (4) with exact softmax confidence distribution.
            </p>
            <div className="pt-2 text-xs font-mono text-brand-400 flex items-center space-x-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Deterministic PyTorch Model</span>
            </div>
          </div>

          {/* Pillar 2 */}
          <div className="glass-panel glass-panel-hover rounded-2xl p-7 border border-surface-700/60 shadow-xl space-y-4">
            <div className="w-12 h-12 rounded-xl bg-medblue-500/10 border border-medblue-500/20 text-medblue-400 flex items-center justify-center">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-surface-100">
              Grad-CAM Explainable AI
            </h3>
            <p className="text-xs sm:text-sm text-surface-400 leading-relaxed">
              Transparent gradient-weighted activation maps computed directly from convolutional feature maps (<code className="text-brand-300 text-[11px]">features[-1]</code>) overlaid on the fundus.
            </p>
            <div className="pt-2 text-xs font-mono text-medblue-400 flex items-center space-x-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Full Visual Interpretability</span>
            </div>
          </div>

          {/* Pillar 3 */}
          <div className="glass-panel glass-panel-hover rounded-2xl p-7 border border-surface-700/60 shadow-xl space-y-4">
            <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center">
              <Activity className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-surface-100">
              Referable DR Risk Assessment
            </h3>
            <p className="text-xs sm:text-sm text-surface-400 leading-relaxed">
              Automated clinical triage dividing cases into Referable vs Non-Referable DR using calibrated decision threshold (<code className="text-amber-300 text-[11px]">0.13</code>) for high sensitivity screening.
            </p>
            <div className="pt-2 text-xs font-mono text-amber-400 flex items-center space-x-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Calibrated 0.13 Cutoff</span>
            </div>
          </div>
        </div>
      </section>

      {/* Validated Model Performance Benchmarks */}
      <section id="benchmarks" className="glass-panel rounded-2xl p-8 sm:p-10 border border-surface-700/80 shadow-2xl space-y-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-surface-800">
          <div>
            <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-brand-400">
              <Database className="w-4 h-4" />
              <span>APTOS Dataset Experimental Evaluation</span>
            </div>
            <h3 className="text-xl sm:text-2xl font-bold text-surface-100 mt-1">
              Verified Model Validation & Test Results
            </h3>
          </div>
          <div className="text-xs text-surface-400 font-mono bg-surface-950 px-3 py-1.5 rounded-lg border border-surface-800">
            Total Dataset: 3,662 Retinal Images
          </div>
        </div>

        {/* 5-Class Per-Grade Metrics Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-surface-800 text-surface-400 font-mono uppercase text-[11px]">
                <th className="pb-3 font-semibold">Severity Grade</th>
                <th className="pb-3 font-semibold">Precision</th>
                <th className="pb-3 font-semibold">Recall</th>
                <th className="pb-3 font-semibold">F1-Score</th>
                <th className="pb-3 font-semibold">Clinical Findings</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-800/60 font-mono text-surface-200">
              <tr>
                <td className="py-3 font-bold text-emerald-400">No DR (Class 0)</td>
                <td className="py-3">0.9949</td>
                <td className="py-3">0.9799</td>
                <td className="py-3 font-bold text-surface-100">0.9873</td>
                <td className="py-3 text-surface-400 font-sans">Normal retinal vasculature and optic disc</td>
              </tr>
              <tr>
                <td className="py-3 font-bold text-blue-400">Mild DR (Class 1)</td>
                <td className="py-3">0.4773</td>
                <td className="py-3">0.7000</td>
                <td className="py-3 font-bold text-surface-100">0.5676</td>
                <td className="py-3 text-surface-400 font-sans">Isolated microaneurysms only</td>
              </tr>
              <tr>
                <td className="py-3 font-bold text-amber-400">Moderate DR (Class 2)</td>
                <td className="py-3">0.7308</td>
                <td className="py-3">0.6552</td>
                <td className="py-3 font-bold text-surface-100">0.6909</td>
                <td className="py-3 text-surface-400 font-sans">Hard exudates, dot hemorrhages, cotton wool</td>
              </tr>
              <tr>
                <td className="py-3 font-bold text-orange-400">Severe DR (Class 3)</td>
                <td className="py-3">0.3333</td>
                <td className="py-3">0.4706</td>
                <td className="py-3 font-bold text-surface-100">0.3902</td>
                <td className="py-3 text-surface-400 font-sans">Extensive intraretinal hemorrhages (&gt;20 in 4 quads)</td>
              </tr>
              <tr>
                <td className="py-3 font-bold text-rose-400">Proliferative DR (Class 4)</td>
                <td className="py-3">0.7083</td>
                <td className="py-3">0.5152</td>
                <td className="py-3 font-bold text-surface-100">0.5965</td>
                <td className="py-3 text-surface-400 font-sans">Neovascularization, vitreous/preretinal hemorrhage</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Aggregate Test Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-surface-800">
          <div className="p-4 rounded-xl bg-surface-950/80 border border-surface-800 text-center">
            <span className="text-[11px] text-surface-400 font-semibold uppercase">Overall Test Accuracy</span>
            <div className="text-xl font-bold font-mono text-surface-100 mt-1">81.42%</div>
          </div>
          <div className="p-4 rounded-xl bg-surface-950/80 border border-surface-800 text-center">
            <span className="text-[11px] text-surface-400 font-semibold uppercase">Test Weighted-F1</span>
            <div className="text-xl font-bold font-mono text-surface-100 mt-1">0.8195</div>
          </div>
          <div className="p-4 rounded-xl bg-surface-950/80 border border-surface-800 text-center">
            <span className="text-[11px] text-surface-400 font-semibold uppercase">Validation Macro-F1</span>
            <div className="text-xl font-bold font-mono text-brand-400 mt-1">0.7012</div>
          </div>
          <div className="p-4 rounded-xl bg-surface-950/80 border border-surface-800 text-center">
            <span className="text-[11px] text-surface-400 font-semibold uppercase">Validation Loss</span>
            <div className="text-xl font-bold font-mono text-surface-100 mt-1">0.7987</div>
          </div>
        </div>
      </section>

      {/* Prominent Medical Disclaimer */}
      <MedicalDisclaimer />
    </div>
  );
};
