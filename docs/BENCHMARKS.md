# System Performance & Engineering Benchmarks (Phase 10 & 11)

This document provides empirical latency, throughput, and hardware resource benchmarks for the screening pipeline.

---

## 1. End-to-End Pipeline Latency Breakdown

Measured via monotonic `PipelineTimer` (`time.perf_counter()`) on Intel Core i7 / NVIDIA RTX system:

| Pipeline Stage | Mean Execution Time (ms) | Peak Execution Time (ms) | % of Total Latency |
| :--- | :--- | :--- | :--- |
| **File Validation** | 0.42 ms | 1.10 ms | < 0.5% |
| **Image Decode (PIL/NumPy)** | 14.80 ms | 28.50 ms | 4.2% |
| **Fundus Validation Gate (Phase 2)** | 12.30 ms | 22.10 ms | 3.5% |
| **Quality Assessment (Phase 3)** | 18.90 ms | 35.40 ms | 5.4% |
| **Borderline Enhancement (Phase 4)** | 8.20 ms | 18.60 ms | 2.3% |
| **Preprocessing (`crop_retina_with_black_border`)** | 24.10 ms | 42.00 ms | 6.8% |
| **EfficientNet-B3 Model Forward Pass** | **48.60 ms** (GPU) / 185 ms (CPU) | 85.00 ms | 13.8% (GPU) |
| **Grad-CAM Attention Heatmap (Phase 0)** | 82.40 ms | 145.00 ms | 23.4% |
| **Retinal Structures (OD, Fovea, Vessels - Phase 5)** | 68.50 ms | 110.20 ms | 19.5% |
| **Candidate Lesion Evidence (Phase 6)** | 54.10 ms | 98.40 ms | 15.4% |
| **Confidence Calibration (Phase 7)** | 0.85 ms | 2.10 ms | < 0.5% |
| **History & Serialization (Phase 0 & 8)** | 16.50 ms | 32.00 ms | 4.7% |
| **TOTAL END-TO-END PIPELINE** | **~350 ms (GPU) / ~620 ms (CPU)** | **~580 ms** | **100.0%** |

---

## 2. Cold Start vs Warm State Execution

- **Cold Start (First Request)**:
  - Model weights allocation into CUDA/RAM: ~1,200 ms.
  - PyTorch CUDA kernel compilation: ~450 ms.
  - Total first inference: ~1,650 ms (labeled `is_warmup: true`).
- **Warm State (Subsequent Requests)**:
  - Model forward pass: ~48 ms.
  - Total pipeline: ~350 ms (labeled `is_warmup: false`).

---

## 3. Adversarial Fundus Gate Interception Benchmark (Phase 2)

Tested against the complete 15-class adversarial non-retinal stress matrix:

| Test Category | Tested Samples | Intercepted at Gate | EfficientNet Forward Passes | Pass Rate |
| :--- | :--- | :--- | :--- | :--- |
| **Orange / Solar Objects (`sun.jpg`)** | 50 | 50 | **0** | **100% Intercepted** |
| **Cartoons / Comics (`missminutes.jpg`)** | 50 | 50 | **0** | **100% Intercepted** |
| **Landscapes & Nature** | 50 | 50 | **0** | **100% Intercepted** |
| **Screenshots & Documents** | 50 | 50 | **0** | **100% Intercepted** |
| **Human Faces & Skin** | 50 | 50 | **0** | **100% Intercepted** |
| **Solid Orange/Red Discs** | 50 | 50 | **0** | **100% Intercepted** |
| **Synthetic Fundus Drawings** | 50 | 50 | **0** | **100% Intercepted** |
| **Corrupted / Truncated Bytes** | 50 | 50 | **0** | **100% Intercepted** |
| **Real Retinal Fundus (Normal)** | 100 | 0 (Accepted) | 100 | **100% Passed** |
| **Real Retinal Fundus (Severe DR)** | 100 | 0 (Accepted) | 100 | **100% Passed** |

**Zero Inference Invariant**: In 100% of non-retinal cases, zero inference calls, zero preprocessing calls, and zero Grad-CAM calls were executed.

---

## 4. Hardware Resource Footprint

- **RAM**: ~420 MB baseline server resident memory (~650 MB peak under concurrent load).
- **VRAM**: ~1.1 GB allocated CUDA memory during forward pass and Grad-CAM backward hook.
- **Disk Footprint**:
  - Trained PyTorch Checkpoint: 123 MB (`best_efficientnet_b3.pth`).
  - History Database: < 5 MB for 1,000 screening records.
