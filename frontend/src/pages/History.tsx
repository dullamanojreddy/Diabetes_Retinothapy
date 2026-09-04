import React, { useState, useEffect } from 'react';
import { History as HistoryIcon, RefreshCw, Eye, Calendar, AlertOctagon, CheckCircle2, X, ShieldAlert, CameraOff } from 'lucide-react';
import { HistoryItem } from '../types/prediction';
import { fetchHistory } from '../services/api';
import { formatDate, formatPercent, getSeverityStyle } from '../utils/formatting';

export const History: React.FC = () => {
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRecord, setSelectedRecord] = useState<HistoryItem | null>(null);

  const loadHistory = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchHistory(50);
      setHistoryItems(data.items);
    } catch (err: any) {
      setError(err.message || 'Failed to load screening history.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  return (
    <div className="space-y-8 py-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-surface-800">
        <div>
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <HistoryIcon className="w-3.5 h-3.5" />
            <span>Audit Trail & Records</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-surface-100 tracking-tight">
            Screening History Log
          </h1>
          <p className="text-xs sm:text-sm text-surface-400 mt-0.5">
            Audit history of completed screenings, quality gate outcomes, and explainability artifacts.
          </p>
        </div>

        <button
          onClick={loadHistory}
          disabled={isLoading}
          className="px-4 py-2 rounded-xl bg-surface-900 hover:bg-surface-800 text-surface-200 border border-surface-700 text-xs font-semibold flex items-center space-x-2 transition-colors self-start sm:self-auto"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-brand-400' : ''}`} />
          <span>Refresh Records</span>
        </button>
      </div>

      {/* Main Content */}
      {isLoading ? (
        <div className="glass-panel rounded-2xl p-12 text-center text-surface-400 text-sm">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-brand-400 mb-2" />
          <span>Loading screening records...</span>
        </div>
      ) : error ? (
        <div className="glass-panel rounded-2xl p-8 text-center text-rose-300 text-sm border-rose-500/30">
          <p>{error}</p>
          <button
            onClick={loadHistory}
            className="mt-4 px-4 py-2 rounded-xl bg-surface-800 text-xs text-surface-200 border border-surface-700"
          >
            Retry
          </button>
        </div>
      ) : historyItems.length === 0 ? (
        <div className="glass-panel rounded-2xl p-12 text-center space-y-3">
          <div className="w-12 h-12 rounded-xl bg-surface-800 flex items-center justify-center mx-auto text-surface-400">
            <HistoryIcon className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-surface-200">No Screening History Yet</h3>
          <p className="text-xs text-surface-400 max-w-sm mx-auto">
            Upload and analyze a retinal fundus image in the Screening tab to automatically record audit entries.
          </p>
        </div>
      ) : (
        <div className="glass-panel rounded-2xl overflow-hidden border border-surface-700/80 shadow-2xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-surface-900/80 border-b border-surface-800 text-surface-400 uppercase text-[11px] font-mono">
                  <th className="py-3.5 px-4 font-semibold">Image & Timestamp</th>
                  <th className="py-3.5 px-4 font-semibold">Outcome / Grade</th>
                  <th className="py-3.5 px-4 font-semibold">Confidence</th>
                  <th className="py-3.5 px-4 font-semibold">Referable Risk</th>
                  <th className="py-3.5 px-4 font-semibold">Visual Artifact</th>
                  <th className="py-3.5 px-4 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-800/60 font-sans">
                {historyItems.map((item) => {
                  const isValid = item.status === 'VALID';
                  const style = getSeverityStyle(item.predicted_class);
                  return (
                    <tr
                      key={item.screening_id || item.id}
                      className="hover:bg-surface-900/40 transition-colors group cursor-pointer"
                      onClick={() => setSelectedRecord(item)}
                    >
                      {/* Image & Timestamp */}
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-3">
                          {item.original_url ? (
                            <img
                              src={item.original_url}
                              alt="Fundus thumb"
                              className="w-10 h-10 rounded-lg object-cover bg-black border border-surface-800 shrink-0"
                            />
                          ) : (
                            <div className="w-10 h-10 rounded-lg bg-surface-900 border border-surface-800 flex items-center justify-center shrink-0 text-surface-500">
                              {item.status === 'INVALID_IMAGE' ? <ShieldAlert className="w-5 h-5 text-amber-400" /> : <CameraOff className="w-5 h-5 text-orange-400" />}
                            </div>
                          )}
                          <div>
                            <span className="font-semibold text-surface-200 block truncate max-w-[160px] sm:max-w-xs" title={item.filename}>
                              {item.filename}
                            </span>
                            <span className="text-[11px] text-surface-400 font-mono flex items-center space-x-1 mt-0.5">
                              <Calendar className="w-3 h-3" />
                              <span>{formatDate(item.timestamp)}</span>
                            </span>
                          </div>
                        </div>
                      </td>

                      {/* Outcome / Grade */}
                      <td className="py-3 px-4">
                        {isValid ? (
                          <span className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-bold ${style.badge}`}>
                            <span>Grade {item.predicted_class}: {item.predicted_class_name}</span>
                          </span>
                        ) : item.status === 'INVALID_IMAGE' ? (
                          <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                            <ShieldAlert className="w-3 h-3" />
                            <span>Rejected (Non-Retinal)</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-orange-500/20 text-orange-300 border border-orange-500/30">
                            <CameraOff className="w-3 h-3" />
                            <span>Rejected (Low Quality)</span>
                          </span>
                        )}
                      </td>

                      {/* Confidence */}
                      <td className="py-3 px-4 font-mono font-semibold text-surface-200">
                        {isValid && item.confidence !== undefined ? formatPercent(item.confidence, 1) : '—'}
                      </td>

                      {/* Referable Risk */}
                      <td className="py-3 px-4">
                        {isValid ? (
                          <div className="flex items-center space-x-1.5">
                            {item.is_referable ? (
                              <span className="text-rose-400 font-semibold flex items-center space-x-1">
                                <AlertOctagon className="w-3.5 h-3.5" />
                                <span>Referable ({formatPercent(item.referable_probability || 0, 1)})</span>
                              </span>
                            ) : (
                              <span className="text-emerald-400 font-semibold flex items-center space-x-1">
                                <CheckCircle2 className="w-3.5 h-3.5" />
                                <span>Non-referable</span>
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-surface-500 font-mono">No prediction</span>
                        )}
                      </td>

                      {/* Overlay Thumbnail */}
                      <td className="py-3 px-4">
                        {item.overlay_url ? (
                          <img
                            src={item.overlay_url}
                            alt="Grad-CAM Overlay thumbnail"
                            className="w-10 h-10 rounded-lg object-cover bg-black border border-brand-500/30"
                          />
                        ) : (
                          <span className="text-surface-500 font-mono text-[11px]">N/A</span>
                        )}
                      </td>

                      {/* Action */}
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedRecord(item);
                          }}
                          className="px-3 py-1.5 rounded-lg bg-surface-800 hover:bg-brand-500/20 text-surface-300 hover:text-brand-300 border border-surface-700 hover:border-brand-500/40 text-xs font-semibold inline-flex items-center space-x-1 transition-colors"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>View</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Detailed Inspection Modal */}
      {selectedRecord && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto animate-in fade-in duration-200">
          <div className="glass-panel max-w-2xl w-full rounded-2xl p-6 sm:p-8 border border-surface-700 shadow-2xl relative space-y-6 my-8">
            <div className="flex items-center justify-between pb-4 border-b border-surface-800">
              <div>
                <span className="text-xs font-mono text-brand-400 font-semibold uppercase">
                  Audit Record: {selectedRecord.status}
                </span>
                <h3 className="text-xl font-bold text-surface-100 mt-0.5">
                  {selectedRecord.filename}
                </h3>
              </div>
              <button
                onClick={() => setSelectedRecord(null)}
                className="p-2 rounded-xl bg-surface-900 hover:bg-surface-800 text-surface-400 hover:text-surface-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Images Visual Comparison */}
            {selectedRecord.original_url && selectedRecord.overlay_url ? (
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5 text-center">
                  <span className="text-xs text-surface-400 font-semibold">Preprocessed Fundus</span>
                  <img
                    src={selectedRecord.original_url}
                    alt="Original"
                    className="w-full aspect-square rounded-xl object-contain bg-black border border-surface-800"
                  />
                </div>
                <div className="space-y-1.5 text-center">
                  <span className="text-xs text-brand-400 font-semibold">Grad-CAM Overlay</span>
                  <img
                    src={selectedRecord.overlay_url}
                    alt="Grad-CAM Overlay"
                    className="w-full aspect-square rounded-xl object-contain bg-black border border-brand-500/30"
                  />
                </div>
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-surface-950 border border-surface-800 text-center text-xs text-surface-400">
                <span>Visual explainability not generated for non-prediction/rejected outcomes.</span>
              </div>
            )}

            {/* Detail Stats */}
            {selectedRecord.status === 'VALID' ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-surface-950/80 border border-surface-800">
                  <span className="text-surface-400 block">Predicted Grade</span>
                  <span className="font-bold text-surface-100 text-sm mt-0.5 block">
                    Grade {selectedRecord.predicted_class}: {selectedRecord.predicted_class_name}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-surface-950/80 border border-surface-800">
                  <span className="text-surface-400 block">Confidence</span>
                  <span className="font-bold font-mono text-surface-100 text-sm mt-0.5 block">
                    {formatPercent(selectedRecord.confidence || 0, 1)}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-surface-950/80 border border-surface-800">
                  <span className="text-surface-400 block">Referable Decision</span>
                  <span className={`font-bold text-sm mt-0.5 block ${selectedRecord.is_referable ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {selectedRecord.is_referable ? 'Referable (Positive)' : 'Non-Referable'}
                  </span>
                </div>
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-surface-950/80 border border-surface-800 text-xs text-surface-300">
                <span className="font-semibold text-amber-400 block mb-1">Rejection Details:</span>
                <span>The image was intercepted by the pre-inference safety gate ({selectedRecord.status}) and safely excluded from model classification.</span>
              </div>
            )}

            <div className="text-[11px] text-surface-400 font-mono flex items-center justify-between">
              <span>Audit ID: {selectedRecord.screening_id || selectedRecord.id}</span>
              <span>Recorded: {formatDate(selectedRecord.timestamp)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
