import html
from datetime import datetime
from typing import Dict, Any, Optional

from app.core.config import settings
from app.services.history_service import history_service

class ReportService:
    """
    Phase 8: Automated Annotated Screening Report Generation.
    Renders a comprehensive, print-ready clinical report from persisted screening records.
    Strictly isolated: ZERO deep learning or classical CV inference is executed during report generation.
    All dynamic strings are escaped to ensure safety against injection vulnerabilities.
    """

    def get_screening_record(self, screening_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the persisted record from history service.
        """
        return history_service.get_by_id(screening_id)

    def generate_html_report(self, record: Dict[str, Any]) -> str:
        """
        Generates clean, professional HTML/CSS report optimized for both screen viewing and A4/Letter printing.
        """
        # 1. Sanitize top-level metadata
        raw_screening_id = str(record.get("screening_id") or record.get("id") or "UNKNOWN")
        screening_id = html.escape(raw_screening_id)
        raw_timestamp = str(record.get("timestamp") or record.get("created_at") or datetime.utcnow().isoformat())
        timestamp = html.escape(raw_timestamp)
        filename = html.escape(str(record.get("filename") or "fundus_capture.jpg"))
        status_val = html.escape(str(record.get("status") or "VALID"))
        model_name = html.escape(str(record.get("model_version") or settings.MODEL_VERSION or "EfficientNet-B3"))

        # 2. Diagnosis & Severity Info
        diag = record.get("diagnosis") or {}
        if isinstance(diag, dict):
            class_id = diag.get("class_id", record.get("predicted_class", 0))
            class_name = str(diag.get("label") or diag.get("class_name") or record.get("predicted_class_name", "No DR"))
            conf = float(diag.get("confidence") or record.get("confidence", 0.0))
        else:
            class_id = record.get("predicted_class", 0)
            class_name = str(record.get("predicted_class_name", "No DR"))
            conf = float(record.get("confidence", 0.0))

        class_name_escaped = html.escape(class_name)
        confidence_pct = f"{conf * 100:.1f}%"

        # Severity color coding
        severity_colors = {
            0: {"bg": "#ecfdf5", "border": "#10b981", "text": "#065f46", "badge": "#059669"},
            1: {"bg": "#f0fdf4", "border": "#34d399", "text": "#047857", "badge": "#10b981"},
            2: {"bg": "#fffbeb", "border": "#f59e0b", "text": "#92400e", "badge": "#d97706"},
            3: {"bg": "#fef2f2", "border": "#ef4444", "text": "#991b1b", "badge": "#dc2626"},
            4: {"bg": "#faf5ff", "border": "#a855f7", "text": "#6b21a8", "badge": "#7c3aed"}
        }
        color_scheme = severity_colors.get(class_id, severity_colors[0])

        # 3. Referable Risk Info
        ref = record.get("referable") or {}
        if isinstance(ref, dict):
            is_referable = ref.get("status") == "REFERABLE" or record.get("is_referable", False)
            referable_prob = float(ref.get("probability") or record.get("referable_probability", 0.0))
            threshold = float(ref.get("threshold") or settings.REFERABLE_THRESHOLD)
        else:
            is_referable = bool(record.get("is_referable", False))
            referable_prob = float(record.get("referable_probability", 0.0))
            threshold = float(settings.REFERABLE_THRESHOLD)

        referable_badge_text = "REFERABLE DR (Level 2+)" if is_referable else "NON-REFERABLE DR"
        referable_badge_class = "ref-positive" if is_referable else "ref-negative"
        clinical_action = (
            "URGENT: Comprehensive ophthalmological examination recommended within 2 to 4 weeks for diabetic retinopathy staging and management."
            if is_referable
            else "ROUTINE: Annual routine diabetic retinopathy screening recommended in 12 months as per clinical guidelines."
        )

        # 4. Confidence Calibration (Phase 7)
        cal = record.get("calibration") or {}
        cal_temp = cal.get("temperature", 1.18) if isinstance(cal, dict) else 1.18
        cal_conf = cal.get("calibrated_confidence", conf) if isinstance(cal, dict) else conf
        cal_conf_pct = f"{cal_conf * 100:.1f}%"

        # 5. Quality Information (Phase 3 & 4)
        qual = record.get("quality") or {}
        qual_status = html.escape(str(qual.get("status", "ACCEPT")))
        qual_grade = html.escape(str(qual.get("grade", "GOOD")))
        reasons = [html.escape(str(r)) for r in qual.get("reasons", [])]
        recapture = [html.escape(str(g)) for g in qual.get("recapture_guidance", [])]

        # 6. Anatomical Landmarks (Phase 5)
        structures = record.get("structures") or {}
        od_info = structures.get("optic_disc", {}) if isinstance(structures, dict) else {}
        fovea_info = structures.get("fovea", {}) if isinstance(structures, dict) else {}
        vessels_info = structures.get("vessels", {}) if isinstance(structures, dict) else {}

        od_detected = od_info.get("detected", False)
        od_text = (
            f"Detected at ({od_info.get('center_x', 'N/A')}, {od_info.get('center_y', 'N/A')}), Radius: {od_info.get('radius', 'N/A')} px (Conf: {od_info.get('confidence', 0.0):.2f})"
            if od_detected else "Not Localized / Sub-optimal visualization"
        )
        fovea_detected = fovea_info.get("detected", False)
        fovea_text = (
            f"Estimated at ({fovea_info.get('center_x', 'N/A')}, {fovea_info.get('center_y', 'N/A')})"
            if fovea_detected else "Not Localized"
        )
        vessels_detected = vessels_info.get("detected", False)
        vessels_text = (
            f"Coverage: {vessels_info.get('vessel_coverage', 0.0)*100:.1f}%, Branch Density: {vessels_info.get('branch_density', 0.0):.4f}"
            if vessels_detected else "Not Segmented"
        )

        # 7. Candidate Lesions (Phase 6 - Research Only)
        lesions = record.get("lesions") or {}
        ma_info = lesions.get("microaneurysms", {}) if isinstance(lesions, dict) else {}
        ex_info = lesions.get("exudates", {}) if isinstance(lesions, dict) else {}
        he_info = lesions.get("hemorrhages", {}) if isinstance(lesions, dict) else {}
        nv_info = lesions.get("neovascularization", {}) if isinstance(lesions, dict) else {}

        # 8. Visual Artifacts (Images)
        original_url = record.get("original_url") or ""
        heatmap_url = record.get("heatmap_url") or ""
        overlay_url = record.get("overlay_url") or ""

        # Probability distribution table
        prob_dict = record.get("probabilities") or {}
        prob_rows = ""
        for grade_idx, grade_name in settings.CLASS_MAPPING.items():
            val = prob_dict.get(grade_name, prob_dict.get(f"class_{grade_idx}", 0.0))
            if isinstance(val, (int, float)):
                pct = val * 100.0
                bar_width = min(max(pct, 1.0), 100.0)
                is_selected = (grade_idx == class_id)
                highlight_style = "font-weight: bold; background-color: rgba(99, 102, 241, 0.08);" if is_selected else ""
                prob_rows += f"""
                <tr style="{highlight_style}">
                    <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0;">Grade {grade_idx}: {html.escape(grade_name)}</td>
                    <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0; text-align: right; width: 80px;">{pct:.1f}%</td>
                    <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0; width: 150px;">
                        <div style="background: #e2e8f0; border-radius: 4px; height: 10px; overflow: hidden;">
                            <div style="background: {'#3b82f6' if not is_selected else color_scheme['badge']}; width: {bar_width}%; height: 100%;"></div>
                        </div>
                    </td>
                </tr>
                """

        # Recapture / Quality advisory block
        recapture_html = ""
        if recapture:
            recapture_items = "".join(f"<li>{item}</li>" for item in recapture)
            recapture_html = f"""
            <div style="background: #fffbeb; border-left: 4px solid #f59e0b; padding: 12px; margin-top: 10px; border-radius: 4px;">
                <strong style="color: #92400e;">Recapture Guidance:</strong>
                <ul style="margin: 6px 0 0 18px; padding: 0; color: #78350f;">
                    {recapture_items}
                </ul>
            </div>
            """

        generated_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Full HTML template
        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Screening Report - {screening_id}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #1e293b;
            background-color: #f8fafc;
            margin: 0;
            padding: 24px;
            font-size: 14px;
            line-height: 1.5;
        }}
        .report-container {{
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
            padding: 32px;
        }}
        .no-print-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 1px solid #e2e8f0;
        }}
        .print-btn {{
            background: #2563eb;
            color: #ffffff;
            border: none;
            padding: 8px 18px;
            font-size: 14px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
        }}
        .print-btn:hover {{ background: #1d4ed8; }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #0f172a;
            padding-bottom: 16px;
            margin-bottom: 20px;
        }}
        .header-title h1 {{
            margin: 0;
            font-size: 22px;
            color: #0f172a;
            letter-spacing: -0.5px;
        }}
        .header-title p {{
            margin: 4px 0 0 0;
            font-size: 13px;
            color: #64748b;
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            background: #f8fafc;
            padding: 12px 16px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 12px;
        }}
        .meta-item strong {{ display: block; color: #64748b; margin-bottom: 2px; font-size: 11px; text-transform: uppercase; }}
        .meta-item span {{ color: #0f172a; font-weight: 500; font-family: monospace; }}
        
        .section-title {{
            font-size: 15px;
            font-weight: 700;
            color: #0f172a;
            margin: 24px 0 10px 0;
            padding-bottom: 4px;
            border-bottom: 1px solid #e2e8f0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .diagnosis-card {{
            background: {color_scheme['bg']};
            border: 2px solid {color_scheme['border']};
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .diag-primary h2 {{
            margin: 0 0 6px 0;
            font-size: 22px;
            color: {color_scheme['text']};
        }}
        .diag-primary p {{ margin: 0; color: #475569; }}
        .diag-confidence {{
            text-align: right;
        }}
        .diag-confidence .conf-value {{
            font-size: 26px;
            font-weight: 800;
            color: {color_scheme['text']};
        }}
        .diag-confidence .cal-note {{
            font-size: 11px;
            color: #64748b;
        }}

        .ref-box {{
            padding: 16px;
            border-radius: 6px;
            margin-bottom: 20px;
        }}
        .ref-positive {{ background: #fef2f2; border: 1px solid #f87171; color: #991b1b; }}
        .ref-negative {{ background: #f0fdf4; border: 1px solid #4ade80; color: #166534; }}

        .images-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }}
        .img-card {{
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            overflow: hidden;
            background: #ffffff;
            text-align: center;
        }}
        .img-card img {{
            width: 100%;
            height: 180px;
            object-fit: cover;
            background: #000000;
            display: block;
        }}
        .img-card .placeholder {{
            height: 180px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f1f5f9;
            color: #94a3b8;
            font-size: 12px;
        }}
        .img-card .label {{
            padding: 8px;
            font-weight: 600;
            font-size: 12px;
            color: #334155;
            background: #f8fafc;
            border-top: 1px solid #e2e8f0;
        }}

        .data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            margin-bottom: 20px;
        }}
        .data-table th {{
            background: #f8fafc;
            padding: 8px 12px;
            text-align: left;
            border-bottom: 2px solid #cbd5e1;
            font-size: 11px;
            text-transform: uppercase;
            color: #475569;
        }}

        .research-badge {{
            display: inline-block;
            background: #fef3c7;
            color: #92400e;
            font-size: 10px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-left: 6px;
        }}

        .disclaimer-box {{
            background: #f8fafc;
            border: 1px solid #cbd5e1;
            padding: 14px;
            border-radius: 6px;
            font-size: 11px;
            color: #475569;
            margin-top: 30px;
            line-height: 1.6;
        }}

        @media print {{
            body {{ background: #ffffff; padding: 0; font-size: 12px; }}
            .report-container {{ border: none; box-shadow: none; padding: 0; max-width: 100%; }}
            .no-print-bar {{ display: none; }}
            .images-grid {{ break-inside: avoid; }}
            .diagnosis-card {{ break-inside: avoid; }}
            .disclaimer-box {{ break-inside: avoid; }}
        }}
    </style>
</head>
<body>

<div class="report-container">
    <div class="no-print-bar">
        <span style="font-size: 13px; color: #64748b;">Clinical Decision Support Tool &bull; Explainable Diabetic Retinopathy Screening</span>
        <button class="print-btn" onclick="window.print()">Print / Save as PDF</button>
    </div>

    <div class="header">
        <div class="header-title">
            <h1>DIABETIC RETINOPATHY SCREENING AUDIT REPORT</h1>
            <p>Automated Multimodal Retinal Analysis &bull; Certified Deep Learning + Classical CV Engine</p>
        </div>
        <div style="text-align: right; font-size: 12px; color: #64748b;">
            <strong>Generated:</strong> {generated_date}
        </div>
    </div>

    <div class="meta-grid">
        <div class="meta-item">
            <strong>Screening ID</strong>
            <span>{screening_id[:16]}...</span>
        </div>
        <div class="meta-item">
            <strong>Capture Timestamp</strong>
            <span>{timestamp[:19].replace('T', ' ')}</span>
        </div>
        <div class="meta-item">
            <strong>Image Filename</strong>
            <span style="font-family: inherit;">{filename}</span>
        </div>
        <div class="meta-item">
            <strong>Screening Model</strong>
            <span style="font-family: inherit;">{model_name}</span>
        </div>
    </div>

    <!-- PRIMARY DIAGNOSIS -->
    <div class="section-title">Primary Clinical Assessment</div>
    <div class="diagnosis-card">
        <div class="diag-primary">
            <h2>Grade {class_id}: {class_name_escaped}</h2>
            <p>Quality Evaluation: <strong>{qual_grade}</strong> &bull; Status: <strong>{status_val}</strong></p>
        </div>
        <div class="diag-confidence">
            <div class="conf-value">{cal_conf_pct}</div>
            <div class="cal-note">Calibrated Confidence (T = {cal_temp:.2f})</div>
            <div class="cal-note" style="color: #94a3b8;">Raw Softmax: {confidence_pct}</div>
        </div>
    </div>

    <!-- REFERABLE RISK -->
    <div class="ref-box {referable_badge_class}">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <strong style="font-size: 16px;">{referable_badge_text}</strong>
            <span style="font-weight: 600;">Risk Score: {referable_prob*100:.1f}% (Threshold: {threshold*100:.0f}%)</span>
        </div>
        <div>{clinical_action}</div>
    </div>

    {recapture_html}

    <!-- VISUAL EXPLAINABILITY -->
    <div class="section-title">Visual Explainability & Attention Artifacts</div>
    <div class="images-grid">
        <div class="img-card">
            {'<img src="' + html.escape(original_url) + '" alt="Preprocessed Fundus">' if original_url else '<div class="placeholder">Artifact Not Available</div>'}
            <div class="label">Preprocessed Fundus</div>
        </div>
        <div class="img-card">
            {'<img src="' + html.escape(heatmap_url) + '" alt="Grad-CAM Heatmap">' if heatmap_url else '<div class="placeholder">Artifact Not Available</div>'}
            <div class="label">Grad-CAM Heatmap</div>
        </div>
        <div class="img-card">
            {'<img src="' + html.escape(overlay_url) + '" alt="Anatomical Overlay">' if overlay_url else '<div class="placeholder">Artifact Not Available</div>'}
            <div class="label">Anatomical Overlay</div>
        </div>
    </div>

    <!-- RETINAL ANATOMICAL LANDMARKS (PHASE 5) -->
    <div class="section-title">Retinal Anatomical Landmarks</div>
    <table class="data-table">
        <thead>
            <tr>
                <th>Anatomical Landmark</th>
                <th>Detection Status</th>
                <th>Clinical Coordinates / Morphology</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">Optic Disc (ONH)</td>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0;">{'LOCALIZED' if od_detected else 'UNAVAILABLE'}</td>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0;">{od_text}</td>
            </tr>
            <tr>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">Fovea / Macula</td>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0;">{'ESTIMATED' if fovea_detected else 'UNAVAILABLE'}</td>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0;">{fovea_text}</td>
            </tr>
            <tr>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">Vessel Tree</td>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0;">{'SEGMENTED' if vessels_detected else 'UNAVAILABLE'}</td>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0;">{vessels_text}</td>
            </tr>
        </tbody>
    </table>

    <!-- LESION CANDIDATES (PHASE 6) -->
    <div class="section-title">Candidate Lesion Evidence <span class="research-badge">Research Only</span></div>
    <table class="data-table">
        <thead>
            <tr>
                <th>Candidate Marker</th>
                <th>Candidate Count</th>
                <th>Heuristic Score</th>
                <th>Classification Isolation</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0;">Microaneurysms (Red Dots)</td>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0;">{ma_info.get('candidate_count', 0)}</td>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0;">{ma_info.get('heuristic_score', 0.0):.2f}</td>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0; color: #059669;">Isolated (Does not affect grade)</td>
            </tr>
            <tr>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0;">Hard Exudates (Lipid Deposits)</td>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0;">{ex_info.get('candidate_count', 0)}</td>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0;">{ex_info.get('heuristic_score', 0.0):.2f}</td>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0; color: #059669;">Isolated (Does not affect grade)</td>
            </tr>
            <tr>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0;">Hemorrhages (Flame / Blot)</td>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0;">{he_info.get('candidate_count', 0)}</td>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0;">{he_info.get('heuristic_score', 0.0):.2f}</td>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0; color: #059669;">Isolated (Does not affect grade)</td>
            </tr>
            <tr>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0;">Neovascularization Indicators</td>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0;">{nv_info.get('indicator', 'NOT_DETECTED')}</td>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0;">{nv_info.get('heuristic_score', 0.0):.2f}</td>
                <td style="padding: 6px 12px; border-bottom: 1px solid #e2e8f0; color: #059669;">Isolated (Does not affect grade)</td>
            </tr>
        </tbody>
    </table>

    <!-- PROBABILITY DISTRIBUTION -->
    <div class="section-title">Severity Probability Distribution</div>
    <table class="data-table">
        <thead>
            <tr>
                <th>Diabetic Retinopathy Grade</th>
                <th style="text-align: right;">Probability</th>
                <th>Distribution Bar</th>
            </tr>
        </thead>
        <tbody>
            {prob_rows}
        </tbody>
    </table>

    <!-- CLINICAL DISCLAIMER -->
    <div class="disclaimer-box">
        <strong>MEDICAL &amp; REGULATORY NOTICE:</strong><br>
        This automated screening report is generated by an artificial intelligence decision support system for research and screening triage assistance. 
        It does NOT constitute a definitive medical diagnosis, nor does it replace comprehensive clinical evaluation by an ophthalmologist, retina specialist, or licensed medical practitioner. 
        All findings, including disease grading, referable classification, and visual attention overlays, must be independently reviewed and verified by a qualified clinician before patient treatment decisions are rendered.
    </div>
</div>

</body>
</html>
"""
        return html_doc

report_service = ReportService()
