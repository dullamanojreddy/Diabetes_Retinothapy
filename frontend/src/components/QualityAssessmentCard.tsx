import React from 'react';
import { CheckCircle2, AlertTriangle, Sparkles, Sliders, Eye, Sun, Camera, ShieldCheck } from 'lucide-react';
import { QualityInfo } from '../types/prediction';

interface QualityAssessmentCardProps {
  quality: QualityInfo;
}

export const QualityAssessmentCard: React.FC<QualityAssessmentCardProps> = ({ quality }) => {
  const grade = quality.grade || (quality.status === 'ACCEPT' ? 'GOOD' : 'ACCEPTABLE');
  const score = quality.score !== undefined ? Math.round(quality.score * 100) : 85;
  const guidance = quality.recapture_guidance || [];

  const metrics = [
    { label: 'Focus & Sharpness', icon: Camera, data: quality.focus },
    { label: 'Illumination', icon: Sun, data: quality.illumination },
    { label: 'Contrast Dynamic Range', icon: Sliders, data: quality.contrast_detail },
    { label: 'Field of View', icon: Eye, data: quality.field_of_view },
    { label: 'Glare & Reflection', icon: ShieldCheck, data: quality.glare },
  ];

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'GOOD':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-950/60 text-emerald-300 border border-emerald-800">Optimal</span>;
      case 'ACCEPTABLE':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-950/60 text-amber-300 border border-amber-800">Acceptable</span>;
      case 'POOR':
      case 'DEGRADED':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-rose-950/60 text-rose-300 border border-rose-800">Degraded</span>;
      default:
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-surface-800 text-surface-300">Verified</span>;
    }
  };

  return (
    <div className="card-glass border border-surface-800/80 rounded-2xl p-6 shadow-xl space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-surface-800">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-emerald-950/60 border border-emerald-800/80 text-emerald-400">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-surface-100 flex items-center gap-2">
              Image Quality & Technical Assessment
              <span className="text-xs px-2 py-0.5 rounded-full bg-surface-800 text-surface-300 font-mono">Phase 3 & 4</span>
            </h3>
            <p className="text-xs text-surface-400">Multi-metric illumination, focus, and aperture verification</p>
          </div>
        </div>

        <div className="flex items-center space-x-2 self-start sm:self-auto">
          <span className="text-xs text-surface-400">Quality Score:</span>
          <span className="text-sm font-bold text-emerald-400 font-mono">{score}%</span>
          <span className="text-xs px-2.5 py-1 rounded-lg font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-700">
            {grade}
          </span>
        </div>
      </div>

      {/* Sub-Metric Matrix */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {metrics.map((m, idx) => {
          const Icon = m.icon;
          return (
            <div key={idx} className="p-3 rounded-xl bg-surface-900/60 border border-surface-800/80 flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <Icon className="w-4 h-4 text-surface-400" />
                <span className="text-xs text-surface-200 font-medium">{m.label}</span>
              </div>
              {getStatusBadge(m.data?.status)}
            </div>
          );
        })}
      </div>

      {/* Enhancement Telemetry Banner (Phase 4) */}
      {quality.enhancement_applied && (
        <div className="p-3 rounded-xl bg-indigo-950/40 border border-indigo-800/60 flex items-center justify-between">
          <div className="flex items-center space-x-2 text-indigo-300 text-xs font-medium">
            <Sparkles className="w-4 h-4 text-indigo-400 shrink-0" />
            <span>Borderline Enhancement Active: LAB CLAHE contrast normalized ({quality.enhancement_method || 'Conservative CLAHE'})</span>
          </div>
          <span className="text-xs px-2 py-0.5 rounded font-mono font-semibold bg-indigo-900/80 text-indigo-200 border border-indigo-700">
            {quality.enhancement_accepted ? 'Accepted' : 'Reverted'}
          </span>
        </div>
      )}

      {/* Recapture Guidance (if any degraded metrics) */}
      {guidance.length > 0 && (
        <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-800/70 space-y-2">
          <div className="flex items-center space-x-2 text-amber-300 text-xs font-bold">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>Clinical Recapture Guidance</span>
          </div>
          <ul className="list-disc list-inside text-xs text-amber-200/90 space-y-1">
            {guidance.map((item, idx) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
