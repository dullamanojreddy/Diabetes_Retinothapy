import React from 'react';
import { Microscope, AlertCircle, Info } from 'lucide-react';
import { LesionEvidenceInfo } from '../types/prediction';

interface LesionEvidenceCardProps {
  lesions?: LesionEvidenceInfo;
}

export const LesionEvidenceCard: React.FC<LesionEvidenceCardProps> = ({ lesions }) => {
  if (!lesions) {
    return null;
  }

  const ma = lesions.microaneurysms;
  const ex = lesions.exudates;
  const he = lesions.hemorrhages;
  const nv = lesions.neovascularization;

  const candidateItems = [
    {
      title: 'Microaneurysms (Red Dots)',
      count: ma?.candidate_count ?? 0,
      score: ma?.heuristic_score ?? 0,
      desc: 'Small circular vascular dilations',
    },
    {
      title: 'Hard Exudates (Lipid Deposits)',
      count: ex?.candidate_count ?? 0,
      score: ex?.heuristic_score ?? 0,
      desc: 'High-contrast yellowish lipid leakages',
    },
    {
      title: 'Intraretinal Hemorrhages',
      count: he?.candidate_count ?? 0,
      score: he?.heuristic_score ?? 0,
      desc: 'Dot, blot, and flame vascular lesions',
    },
    {
      title: 'Neovascularization Signs',
      status: nv?.indicator ?? 'NOT_DETECTED',
      score: nv?.heuristic_score ?? 0,
      desc: 'Abnormal fine vessel cluster heuristics',
    },
  ];

  return (
    <div className="card-glass border border-surface-800/80 rounded-2xl p-6 shadow-xl space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-surface-800">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-amber-950/60 border border-amber-800/80 text-amber-400">
            <Microscope className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-surface-100 flex items-center gap-2">
              Candidate Lesion Evidence
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-950 text-amber-300 border border-amber-700/80 font-mono font-bold tracking-wide uppercase">
                Research Only
              </span>
            </h3>
            <p className="text-xs text-surface-400">Classical CV candidate regions for clinical audit & research (Phase 6)</p>
          </div>
        </div>

        <div className="flex items-center space-x-1.5 text-xs text-amber-400/90 bg-amber-950/40 border border-amber-800/50 px-3 py-1.5 rounded-lg">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          <span>Non-Diagnostic Telemetry</span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {candidateItems.map((item, idx) => (
          <div key={idx} className="p-3.5 rounded-xl bg-surface-900/60 border border-surface-800/80 space-y-1.5">
            <div className="text-xs text-surface-300 font-semibold truncate">{item.title}</div>
            <div className="flex items-baseline justify-between">
              <span className="text-lg font-bold text-surface-100 font-mono">
                {item.count !== undefined ? `${item.count} candidates` : item.status}
              </span>
              <span className="text-xs text-surface-400 font-mono">
                Score: {item.score.toFixed(2)}
              </span>
            </div>
            <div className="text-[11px] text-surface-400 truncate">{item.desc}</div>
          </div>
        ))}
      </div>

      <div className="p-3 rounded-xl bg-surface-900/80 border border-surface-800 flex items-start space-x-2 text-xs text-surface-400">
        <Info className="w-4 h-4 text-surface-400 shrink-0 mt-0.5" />
        <span>
          <strong>Clinical Isolation Safeguard:</strong> Candidate lesion findings are classical CV heuristic markers intended strictly for research and clinician audit. They do NOT modify or alter the deep learning model's diagnostic grading or referable risk assessment.
        </span>
      </div>
    </div>
  );
};
