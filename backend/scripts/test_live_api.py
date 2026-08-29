import sys
from pathlib import Path
import httpx

def main():
    print("=" * 60)
    print("TESTING LIVE FASTAPI SERVER (http://127.0.0.1:8000)")
    print("=" * 60)

    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=30.0) as client:
        # 1. Health Check
        print("\n[1] Testing GET /api/health ...")
        res = client.get("/api/health")
        assert res.status_code == 200, f"Health check failed: {res.status_code}"
        health_data = res.json()
        print("  Response:", health_data)
        assert health_data["status"] == "healthy"
        assert health_data["model_loaded"] is True
        print("  --> HEALTH CHECK: PASS")

        # 2. Prediction with Sample Fundus
        sample_path = Path("frontend/public/samples/sample_proliferative_dr.jpg")
        print(f"\n[2] Testing POST /api/predict with {sample_path} ...")
        with open(sample_path, "rb") as f:
            files = {"file": ("sample_proliferative_dr.jpg", f, "image/jpeg")}
            res = client.post("/api/predict", files=files)
            
        assert res.status_code == 200, f"Prediction failed ({res.status_code}): {res.text}"
        pred_data = res.json()
        print(f"  Success       : {pred_data['success']}")
        print(f"  Prediction ID : {pred_data['id']}")
        print(f"  Predicted DR  : {pred_data['prediction']['class_name']} (Class {pred_data['prediction']['class_id']})")
        print(f"  Confidence    : {pred_data['prediction']['confidence'] * 100:.2f}%")
        print(f"  Referable Prob: {pred_data['referable']['probability'] * 100:.2f}% (Is Referable: {pred_data['referable']['is_referable']})")
        print(f"  Grad-CAM Avail: {pred_data['explainability']['gradcam_available']}")
        print(f"  Heatmap URL   : {pred_data['explainability']['heatmap_url']}")
        print(f"  Overlay URL   : {pred_data['explainability']['overlay_url']}")
        print(f"  Inference Time: {pred_data['inference_time_ms']} ms")
        print("  --> PREDICTION & GRAD-CAM: PASS")

        # 3. Static File Access (Heatmap & Overlay)
        print("\n[3] Testing Static File Retrieval for Generated Artifacts ...")
        heatmap_res = client.get(pred_data["explainability"]["heatmap_url"])
        assert heatmap_res.status_code == 200, f"Failed to retrieve heatmap: {heatmap_res.status_code}"
        overlay_res = client.get(pred_data["explainability"]["overlay_url"])
        assert overlay_res.status_code == 200, f"Failed to retrieve overlay: {overlay_res.status_code}"
        print(f"  Heatmap Size : {len(heatmap_res.content)} bytes (HTTP 200)")
        print(f"  Overlay Size : {len(overlay_res.content)} bytes (HTTP 200)")
        print("  --> STATIC ARTIFACTS SERVING: PASS")

        # 4. History Log Check
        print("\n[4] Testing GET /api/history ...")
        hist_res = client.get("/api/history")
        assert hist_res.status_code == 200, f"History fetch failed: {hist_res.status_code}"
        hist_data = hist_res.json()
        print(f"  Total History Records: {hist_data['total']}")
        assert hist_data["total"] >= 1, "Expected at least 1 recorded screening in history"
        print("  --> HISTORY PERSISTENCE: PASS")

    print("\n" + "=" * 60)
    print("ALL LIVE END-TO-END SERVER CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
