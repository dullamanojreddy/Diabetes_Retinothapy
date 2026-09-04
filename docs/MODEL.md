# Machine Learning Model Specification - EfficientNet-B3

## Model Summary
- **Architecture**: EfficientNet-B3 (PyTorch Torchvision implementation)
- **Parameters**: ~12.2 million parameters (123 MB checkpoint)
- **Input Resolution**: $380 \times 380$ pixels (RGB)
- **Classifier**: `nn.Sequential(nn.Dropout(p=0.3), nn.Linear(1536, 5))`
- **Output**: 5 raw logits $\rightarrow$ Softmax probabilities $\sum_{i=0}^4 P(i) = 1.0$

## Diabetic Retinopathy Class Mapping
| Class ID | Clinical Grade | Description |
| :--- | :--- | :--- |
| **0** | **No DR** | Normal retina, no microaneurysms or lesions |
| **1** | **Mild DR** | Microaneurysms only |
| **2** | **Moderate DR** | More than microaneurysms, but less than severe DR |
| **3** | **Severe DR** | >20 intraretinal hemorrhages in each of 4 quadrants, venous beading in 2+ quadrants, or IRMA in 1+ quadrant |
| **4** | **Proliferative DR** | Neovascularization and/or vitreous/preretinal hemorrhage |

## Dataset Breakdown (APTOS 2019)
- **Total Images**: 3,662 retinal fundus images
- **Train Set**: 2,930 images (80%)
- **Validation Set**: 366 images (10%)
- **Test Set**: 366 images (10%)
- **Partitioning**: Strictly disjoint image IDs across splits.

## Checkpoint Metadata
- **Checkpoint File**: `backend/models/best_efficientnet_b3.pth`
- **Best Epoch**: 7
- **Validation Macro-F1**: 0.701165
- **Validation Loss**: 0.798680

## Test Evaluation Results
### 5-Class Granular Performance
| DR Severity Stage | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: |
| **No DR (Grade 0)** | 0.9949 | 0.9799 | 0.9873 |
| **Mild DR (Grade 1)** | 0.4773 | 0.7000 | 0.5676 |
| **Moderate DR (Grade 2)** | 0.7308 | 0.6552 | 0.6909 |
| **Severe DR (Grade 3)** | 0.3333 | 0.4706 | 0.3902 |
| **Proliferative DR (Grade 4)** | 0.7083 | 0.5152 | 0.5965 |

### Aggregate Test Metrics
- **Overall Accuracy**: 0.8142 (81.42%)
- **Macro-F1**: 0.6465
- **Weighted-F1**: 0.8195

## Referable DR Definition & Cutoff Analysis
- **Definition**: Per SIH clinical guidelines and international diabetic eye screening consensus, **Referable DR is defined as Level 2+** (Moderate DR, Severe DR, or Proliferative DR). Grade 0 (No DR) and Grade 1 (Mild DR) are categorized as non-referable (routine periodic rescreening).
- **Formula**:
  $$P(\text{Referable}) = \sum_{i=2}^4 P(\text{Class } i) = P(\text{Moderate}) + P(\text{Severe}) + P(\text{Proliferative})$$
- **Configured Thresholds**:
  - `REFERABLE_MIN_GRADE = 2`
  - `REFERABLE_THRESHOLD = 0.13`
- **Referable Test Evaluation**:
  - Sensitivity: **0.8540**
  - Specificity: **0.9607**
  - Precision: **0.9286**
  - Accuracy: **0.9208**
  - **ROC-AUC**: **0.9827**

## Explainability (Grad-CAM)
- **Target Layer**: `model.features[-1]` (last convolutional layer of stage 8 in EfficientNet-B3).
- **Output**: Generates a spatial activation map resized to $380 \times 380$, normalized in $[0, 1]$, and colorized with JET colormap for overlay inspection.

## Limitations & Disclaimer
1. The model was trained on high-quality fundus photography and may have decreased confidence on heavily obscured or out-of-focus captures.
2. The system serves as screening support and is not approved as an autonomous medical diagnostic device.
