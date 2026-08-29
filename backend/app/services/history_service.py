import json
import sqlite3
from typing import List, Optional, Dict, Any
from pathlib import Path
from app.core.config import settings
from app.core.logging_config import logger

class HistoryService:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.absolute_history_db_path
        self._init_db()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    predicted_class INTEGER NOT NULL,
                    predicted_class_name TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    referable_probability REAL NOT NULL,
                    is_referable INTEGER NOT NULL,
                    probabilities TEXT NOT NULL,
                    heatmap_url TEXT NOT NULL,
                    overlay_url TEXT NOT NULL,
                    original_url TEXT NOT NULL
                )
            """)
            conn.commit()

    def save(self, record: Dict[str, Any]) -> None:
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO predictions (
                        id, timestamp, filename, predicted_class, predicted_class_name,
                        confidence, referable_probability, is_referable, probabilities,
                        heatmap_url, overlay_url, original_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record["id"],
                    record["timestamp"],
                    record["filename"],
                    record["predicted_class"],
                    record["predicted_class_name"],
                    record["confidence"],
                    record["referable_probability"],
                    1 if record["is_referable"] else 0,
                    json.dumps(record["probabilities"]),
                    record["heatmap_url"],
                    record["overlay_url"],
                    record["original_url"]
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to persist prediction to history DB: {e}")

    def get_all(self, limit: int = 50) -> List[Dict[str, Any]]:
        results = []
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM predictions
                    ORDER BY datetime(timestamp) DESC
                    LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                for row in rows:
                    results.append({
                        "id": row["id"],
                        "timestamp": row["timestamp"],
                        "filename": row["filename"],
                        "predicted_class": row["predicted_class"],
                        "predicted_class_name": row["predicted_class_name"],
                        "confidence": row["confidence"],
                        "referable_probability": row["referable_probability"],
                        "is_referable": bool(row["is_referable"]),
                        "probabilities": json.loads(row["probabilities"]),
                        "heatmap_url": row["heatmap_url"],
                        "overlay_url": row["overlay_url"],
                        "original_url": row["original_url"]
                    })
        except Exception as e:
            logger.error(f"Failed to fetch history from DB: {e}")
        return results

    def get_by_id(self, prediction_id: str) -> Optional[Dict[str, Any]]:
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM predictions WHERE id = ?", (prediction_id,))
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row["id"],
                        "timestamp": row["timestamp"],
                        "filename": row["filename"],
                        "predicted_class": row["predicted_class"],
                        "predicted_class_name": row["predicted_class_name"],
                        "confidence": row["confidence"],
                        "referable_probability": row["referable_probability"],
                        "is_referable": bool(row["is_referable"]),
                        "probabilities": json.loads(row["probabilities"]),
                        "heatmap_url": row["heatmap_url"],
                        "overlay_url": row["overlay_url"],
                        "original_url": row["original_url"]
                    }
        except Exception as e:
            logger.error(f"Failed to fetch prediction {prediction_id} from DB: {e}")
        return None

history_service = HistoryService()
