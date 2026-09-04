import React from 'react';
import { RefreshCw, ArrowLeft } from 'lucide-react';
import { PredictionResponse } from '../types/prediction';
import { PredictionCard } from '../components/PredictionCard';
import { ReferableRisk } from '../components/ReferableRisk';
import { ProbabilityChart } from '../components/ProbabilityChart';
import { GradCAMViewer } from '../components/GradCAMViewer';
import { ScreeningSummary } from '../components/ScreeningSummary';
import { MedicalDisclaimer } from '../components/MedicalDisclaimer';
import { QualityAssessmentCard } from '../components/QualityAssessmentCard';
import { RetinalStructuresCard } from '../components/RetinalStructuresCard';
import { LesionEvidenceCard } from '../components/LesionEvidenceCard';
import { ConfidenceCalibrationCard } from '../components/ConfidenceCalibrationCard';
import { ReportActions } from '../components/ReportActions';

interface ResultsProps {
  result: PredictionResponse;
  onAnalyzeAnother: () => void;
}

export const Results: React.FC<ResultsProps> = ({ result, onAnalyzeAnother }) => {
  const prediction = result.diagnosis || result.prediction;
  const referable = result.referable;
  const probabilities = result.probabilities || {};
  const explainability = result.explainability;
  const filename = result.filename || 'retinal_image.jpg';

  return (
    <div className="space-y-8 py-6">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-surface-800">
        <div>
          <button
            onClick={onAnalyzeAnother}
            className="inline-flex items-center space-x-1.5 text-xs font-semibold text-surface-400 hover:text-brand-400 mb-2 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Screening Upload</span>
          </button>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-surface-100 tracking-tight">
            AI Screening Analysis Dashboard
          </h1>
          <p className="text-xs sm:text-sm text-surface-400 mt-0.5">
            Retinal fundus image evaluation: <span className="font-mono text-surface-200 font-semibold">{filename}</span>
          </p>
        </div>

        <button
          onClick={onAnalyzeAnother}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand-600 to-emerald-500 hover:from-brand-500 hover:to-emerald-400 text-white font-semibold text-xs sm:text-sm shadow-glow-emerald flex items-center justify-center space-x-2 transition-all self-start sm:self-auto hover:scale-105 active:scale-95"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Analyze Another Image</span>
        </button>
      </div>

      {/* Primary 2-Column Prediction Grid */}
      {prediction && referable && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PredictionCard
            prediction={prediction}
            explanationText={result.explanation_text || 'AI screening complete.'}
          />
          <ReferableRisk
            referable={referable}
            recommendationText={result.referral_recommendation || 'Follow-up as advised.'}
          />
        </div>
      )}

      {/* Phase 8 & 10: Report Actions & Monotonic Performance Instrumentation */}
      <ReportActions
        screeningId={result.screening_id || result.id || 'current'}
        timing={result.timing}
      />

      {/* Phase 3 & 4: Image Quality & Technical Evaluation */}
      {result.quality && (
        <QualityAssessmentCard quality={result.quality} />
      )}

      {/* Phase 7: Post-Hoc Confidence Calibration */}
      {prediction && result.calibration && (
        <ConfidenceCalibrationCard
          calibration={result.calibration}
          rawConfidence={prediction.confidence}
        />
      )}

      {/* Probability Distribution */}
      {prediction && (
        <ProbabilityChart
          probabilities={probabilities}
          predictedClassId={prediction.class_id}
        />
      )}

      {/* Grad-CAM Visual Explainability Viewer */}
      {explainability && prediction && (
        <GradCAMViewer
          explainability={explainability}
          classNameTitle={prediction.label || prediction.class_name || `Class ${prediction.class_id}`}
        />
      )}

      {/* Phase 5: Retinal Anatomical Landmarks */}
      <RetinalStructuresCard structures={result.structures} />

      {/* Phase 6: Candidate Lesion Evidence (Research Only) */}
      <LesionEvidenceCard lesions={result.lesions} />

      {/* Audit Summary Card */}
      <ScreeningSummary result={result} />

      {/* Mandatory Medical Disclaimer Banner */}
      <MedicalDisclaimer />
    </div>
  );
};
