import { useState } from 'react';
import { Navbar } from './components/Navbar';
import { Home } from './pages/Home';
import { Screening } from './pages/Screening';
import { History } from './pages/History';
import { usePrediction } from './hooks/usePrediction';
import { Eye } from 'lucide-react';

export function App() {
  const [currentTab, setCurrentTab] = useState<'home' | 'screening' | 'history'>('home');
  const {
    selectedFile,
    previewUrl,
    isLoading,
    error,
    rejection,
    result,
    health,
    selectFile,
    clearFile,
    runAnalysis,
    resetAll,
  } = usePrediction();

  return (
    <div className="min-h-screen flex flex-col bg-surface-950 text-surface-100 selection:bg-brand-500 selection:text-white">
      {/* Top Navbar */}
      <Navbar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        health={health}
        onResetScreening={() => {
          resetAll();
        }}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8">
        {currentTab === 'home' && (
          <Home
            onStartScreening={() => {
              setCurrentTab('screening');
              resetAll();
            }}
          />
        )}

        {currentTab === 'screening' && (
          <Screening
            selectedFile={selectedFile}
            previewUrl={previewUrl}
            isLoading={isLoading}
            error={error}
            rejection={rejection}
            result={result}
            onFileSelected={selectFile}
            onRemoveFile={clearFile}
            onRunAnalysis={() => runAnalysis()}
            onReset={resetAll}
          />
        )}

        {currentTab === 'history' && <History />}
      </main>

      {/* Footer */}
      <footer className="mt-16 border-t border-surface-800/80 bg-surface-950/60 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-surface-400 gap-4">
          <div className="flex items-center space-x-2">
            <div className="w-5 h-5 rounded-md bg-brand-500/20 text-brand-400 flex items-center justify-center">
              <Eye className="w-3.5 h-3.5" />
            </div>
            <span className="font-semibold text-surface-200">
              Explainable DR Screening
            </span>
            <span>•</span>
            <span>EfficientNet-B3 PyTorch Pipeline</span>
          </div>

          <div className="text-center sm:text-right text-[11px] text-surface-400">
            Intended for research and screening support only. Not a medical diagnosis.
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
