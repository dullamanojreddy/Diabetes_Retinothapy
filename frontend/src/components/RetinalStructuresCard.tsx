import React from 'react';
import { Target, GitBranch, Crosshair, MapPin } from 'lucide-react';
import { RetinalStructuresInfo } from '../types/prediction';

interface RetinalStructuresCardProps {
  structures?: RetinalStructuresInfo;
}

export const RetinalStructuresCard: React.FC<RetinalStructuresCardProps> = ({ structures }) => {
  if (!structures || structures.status === 'UNAVAILABLE') {
    return (
      <div className="card-glass border border-surface-800/80 rounded-2xl p-6 shadow-xl space-y-3">
        <div className="flex items-center space-x-3 pb-3 border-b border-surface-800">
          <div className="p-2.5 rounded-xl bg-surface-800/80 text-surface-400">
            <Target className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-surface-200">Retinal Landmark Analysis</h3>
            <p className="text-xs text-surface-400">Anatomical landmarks localization (Phase 5)</p>
          </div>
        </div>
        <div className="p-4 rounded-xl bg-surface-900/60 border border-surface-800 text-xs text-surface-400 text-center">
          Anatomical landmarks sub-optimally visualized or classical CV localization unavailable.
        </div>
      </div>
    );
  }

  const od = structures.optic_disc;
  const fovea = structures.fovea;
  const vessels = structures.vessels;

  return (
    <div className="card-glass border border-surface-800/80 rounded-2xl p-6 shadow-xl space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-surface-800">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-cyan-950/60 border border-cyan-800/80 text-cyan-400">
            <Target className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-surface-100 flex items-center gap-2">
              Retinal Anatomical Landmarks
              <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800/60 font-mono">Phase 5</span>
            </h3>
            <p className="text-xs text-surface-400">Classical CV landmark localization & vascular morphology</p>
          </div>
        </div>

        <span className="text-xs px-2.5 py-1 rounded-lg font-semibold bg-cyan-950/80 text-cyan-300 border border-cyan-800">
          {structures.status}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Optic Disc */}
        <div className="p-3.5 rounded-xl bg-surface-900/60 border border-surface-800/80 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs text-surface-400 font-semibold flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-cyan-400" />
              Optic Disc (ONH)
            </span>
            <span className={`text-[11px] font-bold px-1.5 py-0.5 rounded ${od?.detected ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-surface-800 text-surface-400'}`}>
              {od?.detected ? 'Localized' : 'Unavailable'}
            </span>
          </div>
          {od?.detected ? (
            <div className="text-xs text-surface-200 font-mono space-y-0.5">
              <div>Center: ({od.center_x}, {od.center_y})</div>
              <div>Radius: {od.radius} px &bull; Conf: {(od.confidence || 0).toFixed(2)}</div>
            </div>
          ) : (
            <div className="text-xs text-surface-500 italic">Not resolved</div>
          )}
        </div>

        {/* Fovea */}
        <div className="p-3.5 rounded-xl bg-surface-900/60 border border-surface-800/80 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs text-surface-400 font-semibold flex items-center gap-1.5">
              <Crosshair className="w-3.5 h-3.5 text-indigo-400" />
              Fovea / Macula
            </span>
            <span className={`text-[11px] font-bold px-1.5 py-0.5 rounded ${fovea?.detected ? 'bg-indigo-950 text-indigo-300 border border-indigo-800' : 'bg-surface-800 text-surface-400'}`}>
              {fovea?.detected ? 'Estimated' : 'Unavailable'}
            </span>
          </div>
          {fovea?.detected ? (
            <div className="text-xs text-surface-200 font-mono space-y-0.5">
              <div>Coordinates: ({fovea.center_x}, {fovea.center_y})</div>
              <div className="text-surface-400">Temporal/Macular anchor</div>
            </div>
          ) : (
            <div className="text-xs text-surface-500 italic">Not resolved</div>
          )}
        </div>

        {/* Vessels */}
        <div className="p-3.5 rounded-xl bg-surface-900/60 border border-surface-800/80 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs text-surface-400 font-semibold flex items-center gap-1.5">
              <GitBranch className="w-3.5 h-3.5 text-emerald-400" />
              Vessel Arborization
            </span>
            <span className={`text-[11px] font-bold px-1.5 py-0.5 rounded ${vessels?.detected ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-surface-800 text-surface-400'}`}>
              {vessels?.detected ? 'Segmented' : 'Unavailable'}
            </span>
          </div>
          {vessels?.detected ? (
            <div className="text-xs text-surface-200 font-mono space-y-0.5">
              <div>Coverage: {((vessels.vessel_coverage || 0) * 100).toFixed(1)}%</div>
              <div>Branch Density: {(vessels.branch_density || 0).toFixed(4)}</div>
            </div>
          ) : (
            <div className="text-xs text-surface-500 italic">Not segmented</div>
          )}
        </div>
      </div>
    </div>
  );
};
