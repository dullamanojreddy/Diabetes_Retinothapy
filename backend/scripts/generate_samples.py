import os
from pathlib import Path
import numpy as np
import cv2

def generate_sample_retina(
    dr_grade: int,
    filename: str,
    output_dirs: list[Path]
):
    """
    Generates realistic retinal fundus sample images corresponding to different
    diabetic retinopathy clinical severities for instant testing.
    """
    size = 512
    img = np.zeros((size, size, 3), dtype=np.uint8)
    center = (256, 256)
    radius = 230
    
    # 1. Base retinal background gradient (deep orange-red to reddish-brown)
    for r in range(radius, 0, -1):
        ratio = r / radius
        r_val = int(180 + 35 * (1 - ratio))
        g_val = int(75 + 25 * (1 - ratio))
        b_val = int(25 + 15 * (1 - ratio))
        cv2.circle(img, center, r, (b_val, g_val, r_val), -1)
        
    # 2. Optic disc (yellowish-white oval on nasal side)
    disc_center = (170, 256)
    cv2.ellipse(img, disc_center, (35, 42), 0, 0, 360, (120, 215, 245), -1)
    cv2.ellipse(img, disc_center, (20, 26), 0, 0, 360, (160, 235, 255), -1)
    
    # 3. Macula (darker reddish-brown zone on temporal side)
    macula_center = (330, 256)
    cv2.circle(img, macula_center, 40, (15, 50, 140), -1)
    cv2.circle(img, macula_center, 12, (10, 35, 110), -1)
    
    # 4. Major retinal vascular arches (arterioles & venules branching from optic disc)
    cv2.ellipse(img, (230, 180), (100, 70), 20, 120, 320, (15, 20, 100), 4) # Superior temporal arcade
    cv2.ellipse(img, (230, 330), (100, 70), -20, 40, 240, (15, 20, 100), 4) # Inferior temporal arcade
    cv2.line(img, disc_center, (120, 160), (15, 20, 100), 3) # Superior nasal
    cv2.line(img, disc_center, (120, 350), (15, 20, 100), 3) # Inferior nasal
    
    # Smaller vessel branches
    cv2.line(img, (260, 140), (360, 120), (20, 25, 110), 2)
    cv2.line(img, (270, 370), (380, 390), (20, 25, 110), 2)
    cv2.line(img, (200, 160), (280, 220), (20, 30, 120), 2)

    # 5. Add grade-specific pathological lesions:
    np.random.seed(42 + dr_grade)
    
    if dr_grade >= 1:
        # Microaneurysms: Tiny deep red dots
        num_ma = 8 if dr_grade == 1 else (20 if dr_grade == 2 else 45)
        for _ in range(num_ma):
            mx = np.random.randint(220, 420)
            my = np.random.randint(160, 360)
            cv2.circle(img, (mx, my), np.random.randint(2, 4), (10, 10, 80), -1)
            
    if dr_grade >= 2:
        # Hard Exudates (bright yellow lipid deposits) & Dot Hemorrhages
        for _ in range(12):
            ex_x = np.random.randint(270, 390)
            ex_y = np.random.randint(200, 320)
            cv2.circle(img, (ex_x, ex_y), np.random.randint(3, 7), (100, 225, 245), -1)
        for _ in range(15):
            hx = np.random.randint(200, 420)
            hy = np.random.randint(150, 380)
            cv2.ellipse(img, (hx, hy), (np.random.randint(4, 9), np.random.randint(3, 6)), np.random.randint(0, 180), 0, 360, (10, 15, 75), -1)

    if dr_grade >= 3:
        # Severe: Extensive blot hemorrhages, cotton wool spots (fluffy white/grey)
        for _ in range(10):
            cwx = np.random.randint(200, 380)
            cwy = np.random.randint(170, 350)
            cv2.circle(img, (cwx, cwy), np.random.randint(10, 18), (170, 180, 190), -1)
        for _ in range(25):
            hx = np.random.randint(160, 440)
            hy = np.random.randint(140, 420)
            cv2.circle(img, (hx, hy), np.random.randint(6, 14), (10, 10, 70), -1)

    if dr_grade >= 4:
        # Proliferative: Fronds of neovascularization (fine tangled network) & large preretinal hemorrhage
        for _ in range(40):
            nx = np.random.randint(160, 240)
            ny = np.random.randint(210, 300)
            cv2.line(img, (nx, ny), (nx + np.random.randint(-15, 15), ny + np.random.randint(-15, 15)), (10, 10, 95), 1)
        # Large preretinal boat-shaped hemorrhage
        cv2.ellipse(img, (310, 220), (35, 18), 15, 0, 180, (5, 5, 60), -1)

    # Save to all output directories
    for out_dir in output_dirs:
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / filename
        cv2.imwrite(str(out_path), img)
        print(f"Created sample fundus: {out_path}")

def generate_all_samples():
    sample_dirs = [
        Path("backend/storage/samples"),
        Path("frontend/public/samples")
    ]
    samples = [
        (0, "sample_no_dr.jpg"),
        (1, "sample_mild_dr.jpg"),
        (2, "sample_moderate_dr.jpg"),
        (3, "sample_severe_dr.jpg"),
        (4, "sample_proliferative_dr.jpg")
    ]
    for grade, fname in samples:
        generate_sample_retina(grade, fname, sample_dirs)

if __name__ == "__main__":
    generate_all_samples()
