import React from 'react';
import { Activity } from 'lucide-react';
import { ImageUploader } from '../components/ImageUploader';
import { ImagePreview } from '../components/ImagePreview';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { Results } from './Results';
import { MedicalDisclaimer } from '../components/MedicalDisclaimer';
import { PredictionResponse } from '../types/prediction';

import { RejectionDetail } from '../hooks/usePrediction';

interface ScreeningProps {
  selectedFile: File | null;
  previewUrl: string | null;
  isLoading: boolean;
  error: string | null;
  rejection?: RejectionDetail | null;
  result: PredictionResponse | null;
  onFileSelected: (file: File) => void;
  onRemoveFile: () => void;
  onRunAnalysis: () => void;
  onReset: () => void;
}

export const Screening: React.FC<ScreeningProps> = ({
  selectedFile,
  previewUrl,
  isLoading,
  error,
  rejection,
  result,
  onFileSelected,
  onRemoveFile,
  onRunAnalysis,
  onReset,
}) => {
  if (result) {
    return <Results result={result} onAnalyzeAnother={onReset} />;
  }

  return (
    <div className="space-y-8 py-6">
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto space-y-2">
        <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-xs font-semibold uppercase tracking-wider">
          <Activity className="w-3.5 h-3.5" />
          <span>Interactive Fundus Screening</span>
        </div>
        <h1 className="text-2xl sm:text-4xl font-extrabold text-surface-100 tracking-tight">
          Retinal Image AI Screening
        </h1>
        <p className="text-xs sm:text-sm text-surface-400">
          Upload a color retinal fundus photograph to classify diabetic retinopathy severity and view Grad-CAM explainability.
        </p>
      </div>

      {/* Main Container */}
      <div className="max-w-4xl mx-auto">
        {isLoading ? (
          <LoadingState />
        ) : error || rejection ? (
          <ErrorState
            status={rejection?.status || 'API_ERROR'}
            message={rejection?.message || error || 'Screening could not be completed.'}
            reasons={rejection?.reasons || []}
            screeningId={rejection?.screeningId}
            onRetry={onReset}
          />
        ) : selectedFile && previewUrl ? (
          <ImagePreview
            file={selectedFile}
            previewUrl={previewUrl}
            onRemove={onRemoveFile}
            onAnalyze={onRunAnalysis}
            disabled={isLoading}
          />
        ) : (
          <ImageUploader onFileSelected={onFileSelected} disabled={isLoading} />
        )}
      </div>

      {/* Medical Disclaimer Banner */}
      <div className="max-w-4xl mx-auto pt-4">
        <MedicalDisclaimer compact />
      </div>
    </div>
  );
};
