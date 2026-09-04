import { useState, useEffect, useCallback } from 'react';
import { PredictionResponse, HealthStatus, ReadinessStatus } from '../types/prediction';
import { screenFundusImage, fetchHealth, fetchReadiness, ScreeningRejectionError } from '../services/api';

export type ScreeningState = 
  | 'IDLE' 
  | 'FILE_SELECTED' 
  | 'ANALYZING' 
  | 'VALID_RESULT' 
  | 'INVALID_FILE' 
  | 'INVALID_IMAGE' 
  | 'LOW_QUALITY' 
  | 'API_ERROR';

export interface RejectionDetail {
  status: 'INVALID_FILE' | 'INVALID_IMAGE' | 'LOW_QUALITY' | 'API_ERROR';
  message: string;
  reasons: string[];
  screeningId?: string;
}

export function usePrediction() {
  const [screeningState, setScreeningState] = useState<ScreeningState>('IDLE');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [rejection, setRejection] = useState<RejectionDetail | null>(null);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [readiness, setReadiness] = useState<ReadinessStatus | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      const hData = await fetchHealth();
      setHealth(hData);
      const rData = await fetchReadiness();
      setReadiness(rData);
    } catch (err) {
      console.warn('Backend health check error:', err);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  const selectFile = useCallback((file: File) => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setError(null);
    setRejection(null);
    setResult(null);
    setScreeningState('FILE_SELECTED');
  }, [previewUrl]);

  const clearFile = useCallback(() => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    setError(null);
    setRejection(null);
    setResult(null);
    setScreeningState('IDLE');
  }, [previewUrl]);

  const runAnalysis = useCallback(async (targetClass?: number) => {
    if (!selectedFile || isLoading) return;

    setIsLoading(true);
    setError(null);
    setRejection(null);
    setScreeningState('ANALYZING');

    try {
      const response = await screenFundusImage(selectedFile, targetClass);
      setResult(response);
      setScreeningState('VALID_RESULT');
    } catch (err: any) {
      if (err instanceof ScreeningRejectionError) {
        setRejection({
          status: err.status,
          message: err.message,
          reasons: err.reasons,
          screeningId: err.screening_id
        });
        setError(err.message);
        setScreeningState(err.status as ScreeningState);
      } else {
        const fallbackMsg = err.message || 'An unexpected connection or server error occurred.';
        setError(fallbackMsg);
        setRejection({
          status: 'API_ERROR',
          message: fallbackMsg,
          reasons: [fallbackMsg]
        });
        setScreeningState('API_ERROR');
      }
    } finally {
      setIsLoading(false);
    }
  }, [selectedFile, isLoading]);

  const resetAll = useCallback(() => {
    clearFile();
    setResult(null);
    setError(null);
    setRejection(null);
    setScreeningState('IDLE');
  }, [clearFile]);

  return {
    screeningState,
    selectedFile,
    previewUrl,
    isLoading,
    error,
    rejection,
    result,
    health,
    readiness,
    selectFile,
    clearFile,
    runAnalysis,
    resetAll,
    checkHealth,
  };
}
