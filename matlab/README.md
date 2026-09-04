# MATLAB Research Evidence Suite (Phase 12)

This directory provides classical computer vision and statistical analysis scripts in MATLAB to complement the Python deep learning screening engine with independent biomedical research evidence.

---

## 1. Directory Structure

```text
matlab/
├── image_quality/
│   └── assess_quality.m       # Quality metrics: Laplacian blur, illumination, contrast, FOV
├── enhancement/
│   └── enhance_fundus.m       # Conservative LAB CLAHE contrast enhancement
├── retinal_analysis/
│   └── segment_vessels.m      # Green channel morphological vessel tree segmentation
├── benchmarks/
│   └── import_predictions.m   # Imports Python predictions CSV, plots histograms & class distributions
└── README.md                  # This guide
```

---

## 2. Prerequisites & MATLAB Toolboxes

- **MATLAB Version**: R2020a or later.
- **Toolboxes**:
  - Image Processing Toolbox (`adapthisteq`, `imtophat`, `bwmorph`, `imbinarize`, `adaptthresh`)
  - Statistics and Machine Learning Toolbox (`histcounts`, `prctile`)

---

## 3. Usage Instructions

### A. Assessing Retinal Image Quality
```matlab
% In MATLAB Command Window:
addpath('image_quality');
quality = assess_quality('path/to/fundus_image.jpg');
disp(quality);
```

### B. Applying Conservative Fundus Enhancement
```matlab
addpath('enhancement');
enhanced = enhance_fundus('path/to/borderline_fundus.jpg', 'enhanced_output.jpg');
imshowpair(imread('path/to/borderline_fundus.jpg'), enhanced, 'montage');
title('Original (Left) vs LAB CLAHE Enhanced (Right)');
```

### C. Segmenting the Retinal Vascular Arborization
```matlab
addpath('retinal_analysis');
[vessels, skel, stats] = segment_vessels('path/to/fundus_image.jpg');

figure;
subplot(1, 2, 1); imshow(vessels); title(sprintf('Vessels (Coverage: %.1f%%)', stats.vessel_coverage*100));
subplot(1, 2, 2); imshow(skel);    title(sprintf('Skeleton (%d Branch Points)', stats.num_branch_points));
```

### D. Importing Python Predictions for Statistical Analysis
First, export the screening predictions from the Python backend:
```powershell
# In Windows PowerShell:
cd backend
.\.venv\Scripts\python scripts/export_predictions.py
```
Then load and analyze them in MATLAB:
```matlab
addpath('benchmarks');
stats = import_predictions('../backend/benchmarks/exports/screening_predictions.csv');
disp(stats);
```
Outputs statistical distributions, referable risk stratification (Level 2+), and generates publication-grade distribution figures.
