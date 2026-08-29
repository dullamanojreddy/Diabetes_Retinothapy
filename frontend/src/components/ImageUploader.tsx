import React, { useRef, useState } from 'react';
import { UploadCloud, Image as ImageIcon, Sparkles, AlertCircle, FileCheck } from 'lucide-react';
import { formatFileSize } from '../utils/formatting';

interface ImageUploaderProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

const SAMPLE_IMAGES = [
  { name: 'Normal (No DR)', file: 'sample_no_dr.jpg', grade: 0, desc: 'Clear retina, normal optic disc and vessels' },
  { name: 'Mild DR', file: 'sample_mild_dr.jpg', grade: 1, desc: 'Microaneurysms visible' },
  { name: 'Moderate DR', file: 'sample_moderate_dr.jpg', grade: 2, desc: 'Hard exudates & dot hemorrhages' },
  { name: 'Severe DR', file: 'sample_severe_dr.jpg', grade: 3, desc: 'Multiple quadrant blot hemorrhages' },
  { name: 'Proliferative DR', file: 'sample_proliferative_dr.jpg', grade: 4, desc: 'Neovascularization & preretinal lesion' },
];

export const ImageUploader: React.FC<ImageUploaderProps> = ({ onFileSelected, disabled = false }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [loadingSample, setLoadingSample] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndSelect = (file: File) => {
    setErrorMessage(null);
    const validTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(jpe?g|png|webp)$/i)) {
      setErrorMessage('Please select a valid retinal image (JPG, PNG, or WEBP).');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setErrorMessage('Image size exceeds maximum limit of 10MB.');
      return;
    }

    onFileSelected(file);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSelect(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleSampleClick = async (sampleFile: string, sampleName: string) => {
    if (disabled) return;
    setLoadingSample(sampleName);
    try {
      const response = await fetch(`/samples/${sampleFile}`);
      if (!response.ok) {
        throw new Error('Failed to load sample image');
      }
      const blob = await response.blob();
      const file = new File([blob], sampleFile, { type: 'image/jpeg' });
      validateAndSelect(file);
    } catch (err) {
      setErrorMessage('Could not load sample fundus image. Please upload a local file.');
    } finally {
      setLoadingSample(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Drag & Drop Main Card */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => !disabled && fileInputRef.current?.click()}
        className={`relative group rounded-2xl border-2 border-dashed transition-all duration-300 cursor-pointer overflow-hidden p-8 sm:p-12 text-center ${
          isDragging
            ? 'border-brand-400 bg-brand-950/40 shadow-glow-emerald scale-[1.01]'
            : 'border-surface-700 hover:border-brand-500/60 bg-surface-900/50 hover:bg-surface-900/80 shadow-lg'
        } ${disabled ? 'opacity-50 pointer-events-none' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png, image/jpeg, image/jpg, image/webp"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              validateAndSelect(e.target.files[0]);
            }
          }}
        />

        {/* Inner Graphic */}
        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-gradient-to-tr from-brand-500/20 via-medblue-500/20 to-brand-400/20 border border-brand-500/30 flex items-center justify-center text-brand-400 group-hover:scale-110 group-hover:text-brand-300 transition-all duration-300 shadow-md">
            <UploadCloud className="w-8 h-8 sm:w-10 sm:h-10" />
          </div>

          <div>
            <h3 className="text-lg sm:text-xl font-bold text-surface-100 group-hover:text-brand-300 transition-colors">
              Upload Retinal Fundus Image
            </h3>
            <p className="text-xs sm:text-sm text-surface-400 mt-1.5 max-w-md mx-auto">
              Drag & drop your fundus photograph here, or <span className="text-brand-400 font-semibold underline underline-offset-2">browse files</span> from your computer.
            </p>
          </div>

          <div className="flex items-center space-x-2 text-[11px] font-mono text-surface-400 bg-surface-950/60 px-3 py-1.5 rounded-full border border-surface-800">
            <span>PNG • JPG • JPEG • WEBP</span>
            <span>•</span>
            <span>Max 10 MB</span>
          </div>
        </div>

        {/* Hover Highlight Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-brand-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
      </div>

      {errorMessage && (
        <div className="bg-rose-950/50 border border-rose-500/40 rounded-xl p-3.5 text-xs sm:text-sm text-rose-200 flex items-center space-x-2.5">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Quick Test Samples */}
      <div className="bg-surface-900/40 border border-surface-800 rounded-xl p-4 sm:p-5">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2 text-xs font-semibold text-surface-300 uppercase tracking-wider">
            <Sparkles className="w-4 h-4 text-brand-400" />
            <span>Or Try Verified Sample Fundus Images</span>
          </div>
          <span className="text-[11px] text-surface-400">1-click test</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5">
          {SAMPLE_IMAGES.map((sample) => (
            <button
              key={sample.file}
              type="button"
              disabled={disabled || loadingSample !== null}
              onClick={(e) => {
                e.stopPropagation();
                handleSampleClick(sample.file, sample.name);
              }}
              className="group/sample text-left p-2.5 rounded-lg bg-surface-950/60 hover:bg-surface-800 border border-surface-800 hover:border-brand-500/40 transition-all text-xs flex flex-col justify-between"
            >
              <div>
                <div className="font-semibold text-surface-200 group-hover/sample:text-brand-300 transition-colors">
                  {sample.name}
                </div>
                <div className="text-[10px] text-surface-400 mt-1 line-clamp-1">
                  {sample.desc}
                </div>
              </div>
              <div className="mt-2 text-[10px] font-mono text-brand-400/80 group-hover/sample:text-brand-300 flex items-center space-x-1">
                <span>Select & Analyze</span>
                <span>→</span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
