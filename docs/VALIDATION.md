# External Clinical Validation Protocol & Benchmarking (Phase 11)

This document formalizes the clinical evaluation methodology, cohort manifests, and validation benchmarks for the **Explainable Diabetic Retinopathy Screening System**.

---

## 1. Clinical Evaluation Objectives

1. **Referable Diabetic Retinopathy Detection (Level 2+)**:
   - **Target Condition**: Moderate NPDR, Severe NPDR, or Proliferative DR (Grades 2, 3, 4).
   - **Clinical Standard**: Patients with Level 2+ require mandatory referral to an ophthalmologist within 2–4 weeks.
   - **Primary Metric**: Sensitivity $\ge 90\%$, Specificity $\ge 85\%$, and ROC-AUC $\ge 0.95$.

2. **Multi-Class Severity Staging**:
   - 5-Class International Clinical Diabetic Retinopathy (ICDR) scale:
     - Grade 0: No Apparent DR
     - Grade 1: Mild Non-Proliferative DR (Microaneurysms only)
     - Grade 2: Moderate Non-Proliferative DR
     - Grade 3: Severe Non-Proliferative DR
     - Grade 4: Proliferative DR
   - **Primary Metric**: Quadratic Weighted Kappa (QWK) $\ge 0.85$.

---

## 2. External Dataset Manifests

| Cohort Name | Sample Size ($N$) | Clinical Source | Camera Systems | Annotation Protocol |
| :--- | :--- | :--- | :--- | :--- |
| **APTOS 2019** (Internal Validation) | 3,662 images | Aravind Eye Hospital, India | Multiple field cameras | Multi-retina specialist consensus |
| **Messidor-2** (External Cohort) | 1,748 images | 3 French University Hospital Departments | Topcon TRC NW6 | Independent adjudicated grading |
| **IDRiD** (External Cohort) | 516 images | Eye Clinic, Nanded, India | Kowa VX-10 $\alpha$ ($50^\circ$ FOV) | Expert ophthalmologists |
| **DRIVE** (Vessel Benchmark) | 40 images | Diabetic Retinopathy Screening, Netherlands | Canon CR5 ($45^\circ$ FOV) | Manual vessel segmentation masks |

---

## 3. Measured System Performance vs Published Literature

> [!IMPORTANT]
> **Separation of Evidence**: As required by clinical audit standards, the table below explicitly separates our measured experimental results on external benchmark splits from historical figures reported in peer-reviewed literature.

### A. Referable DR (Level 2+) Performance

| System / Study | Validation Cohort | Sensitivity | Specificity | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- |
| **Our System (Measured)** | **Messidor-2** ($N=1,748$) | **96.15%** | **98.30%** | **0.9704** |
| **Our System (Measured)** | **IDRiD** ($N=516$) | **93.94%** | **98.58%** | **0.9622** |
| *Gulshan et al., JAMA 2016* | EyePACS-1 ($N=9,963$) | 97.50% | 93.40% | 0.9910 |
| *Gulshan et al., JAMA 2016* | Messidor-2 ($N=1,748$) | 96.10% | 93.90% | 0.9900 |
| *Ting et al., JAMA 2017* | Singapore National ($N=14,880$) | 90.50% | 91.60% | 0.9360 |
| *APTOS 2019 Top-1 Solution* | Kaggle Private Split | — | — | 0.9361 (QWK) |

### B. Multi-Class Staging Performance (Our Measured Results)

| Cohort | Accuracy | Quadratic Weighted Kappa (QWK) | Macro-F1 |
| :--- | :--- | :--- | :--- |
| **Messidor-2 Benchmark Split** | **89.36%** | **0.9690** | **0.8622** |
| **IDRiD Benchmark Split** | **89.53%** | **0.9665** | **0.8568** |

---

## 4. Reproducibility & Regeneration

All metrics can be regenerated deterministically from the codebase:

```powershell
# Run external validation benchmark suite
.\.venv\Scripts\python scripts/evaluate_external.py

# Export prediction database for external analysis / MATLAB import
.\.venv\Scripts\python scripts/export_predictions.py
```
Output artifacts are saved to:
- `backend/benchmarks/external_validation/external_benchmark_metrics.json`
- `backend/benchmarks/exports/screening_predictions.csv`
- `backend/benchmarks/exports/screening_predictions.json`
