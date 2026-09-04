import React from 'react';
import { Eye, Activity, History, Home, Sparkles } from 'lucide-react';
import { HealthStatus } from '../types/prediction';

interface NavbarProps {
  currentTab: 'home' | 'screening' | 'history';
  setCurrentTab: (tab: 'home' | 'screening' | 'history') => void;
  health: HealthStatus | null;
  onResetScreening?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  setCurrentTab,
  health,
  onResetScreening
}) => {
  return (
    <header className="sticky top-0 z-50 bg-surface-950/80 backdrop-blur-md border-b border-surface-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div 
            className="flex items-center space-x-3 cursor-pointer group"
            onClick={() => setCurrentTab('home')}
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-medblue-500 p-0.5 shadow-lg shadow-brand-500/20 group-hover:scale-105 transition-transform duration-200">
              <div className="w-full h-full bg-surface-950 rounded-[10px] flex items-center justify-center">
                <Eye className="w-5 h-5 text-brand-400 group-hover:text-brand-300 transition-colors" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-base sm:text-lg tracking-tight bg-gradient-to-r from-surface-100 via-surface-200 to-brand-300 bg-clip-text text-transparent">
                  Explainable DR
                </span>
                <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-brand-500/10 text-brand-400 border border-brand-500/20">
                  AI Screening
                </span>
              </div>
              <p className="text-[11px] text-surface-400 hidden sm:block">
                EfficientNet-B3 • Grad-CAM Explainability
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex items-center space-x-1 sm:space-x-2">
            <button
              onClick={() => setCurrentTab('home')}
              className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium flex items-center space-x-1.5 transition-all ${
                currentTab === 'home'
                  ? 'bg-surface-800 text-surface-100 border border-surface-700 shadow-sm'
                  : 'text-surface-400 hover:text-surface-200 hover:bg-surface-900'
              }`}
            >
              <Home className="w-4 h-4" />
              <span>Overview</span>
            </button>

            <button
              onClick={() => {
                setCurrentTab('screening');
                if (onResetScreening) onResetScreening();
              }}
              className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium flex items-center space-x-1.5 transition-all ${
                currentTab === 'screening'
                  ? 'bg-brand-500/20 text-brand-300 border border-brand-500/40 shadow-glow-emerald'
                  : 'text-surface-400 hover:text-surface-200 hover:bg-surface-900'
              }`}
            >
              <Activity className="w-4 h-4 text-brand-400" />
              <span>Screening</span>
            </button>

            <button
              onClick={() => setCurrentTab('history')}
              className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium flex items-center space-x-1.5 transition-all ${
                currentTab === 'history'
                  ? 'bg-surface-800 text-surface-100 border border-surface-700 shadow-sm'
                  : 'text-surface-400 hover:text-surface-200 hover:bg-surface-900'
              }`}
            >
              <History className="w-4 h-4" />
              <span>History</span>
            </button>
          </nav>

          {/* Backend System Status */}
          <div className="hidden md:flex items-center space-x-3">
            <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-surface-900 border border-surface-800 text-xs">
              <span className={`w-2 h-2 rounded-full ${health?.model_loaded ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
              <span className="text-surface-300 font-mono text-[11px]">
                {health ? `${health.model} (${health.device})` : 'Connecting...'}
              </span>
            </div>

            <button
              onClick={() => {
                setCurrentTab('screening');
                if (onResetScreening) onResetScreening();
              }}
              className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-brand-600 to-emerald-500 hover:from-brand-500 hover:to-emerald-400 text-white text-xs font-semibold shadow-md shadow-brand-600/20 flex items-center space-x-1.5 transition-all hover:scale-105 active:scale-95"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>New Screen</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
