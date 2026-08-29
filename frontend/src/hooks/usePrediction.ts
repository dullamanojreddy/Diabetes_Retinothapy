import { useState, useEffect, useCallback } from 'react';
import { PredictionResponse, HealthStatus } from '../types/prediction';
import { predictFundusImage, fetchHealth } from '../services/api';

export function usePrediction() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      const data = await fetchHealth();
      setHealth(data);
    } catch (err) {
      console.warn('Backend health check error:', err);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 20000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  const selectFile = useCallback((file: File) => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setError(null);
    setResult(null);
  }, [previewUrl]);

  const clearFile = useCallback(() => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    setError(null);
    setResult(null);
  }, [previewUrl]);

  const runAnalysis = useCallback(async (targetClass?: number) => {
    if (!selectedFile) return;

    setIsLoading(true);
    setError(null);

    try {
      const predictionResponse = await predictFundusImage(selectedFile, targetClass);
      setResult(predictionResponse);
    } catch (err: any) {
      setError(err.message || 'An error occurred while running AI screening.');
    } finally {
      setIsLoading(false);
    }
  }, [selectedFile]);

  const resetAll = useCallback(() => {
    clearFile();
    setResult(null);
    setError(null);
  }, [clearFile]);

  return {
    selectedFile,
    previewUrl,
    isLoading,
    error,
    result,
    health,
    selectFile,
    clearFile,
    runAnalysis,
    resetAll,
    checkHealth,
  };
}
