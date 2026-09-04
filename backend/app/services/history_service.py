import json
import threading
from typing import List, Optional, Dict, Any
from pathlib import Path

from app.core.config import settings
from app.core.logging_config import logger

class HistoryService:
    """
    Local JSON file-based history index as specified in Section 9 of the blueprint.
    Persists completed screenings and non-prediction outcomes without SQLite/DB complexity.
    """
    def __init__(self, history_file: Optional[Path] = None):
        self.history_file = history_file or settings.absolute_history_file
        self._lock = threading.Lock()
        self._init_store()

    def _init_store(self):
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.history_file.exists():
            with self._lock:
                try:
                    with open(self.history_file, "w", encoding="utf-8") as f:
                        json.dump([], f)
                except Exception as e:
                    logger.error(f"Failed to initialize history store: {e}")

    def _load_all(self) -> List[Dict[str, Any]]:
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Failed to read history from {self.history_file}: {e}")
            return []

    def _save_all(self, records: List[Dict[str, Any]]) -> None:
        try:
            temp_file = self.history_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            temp_file.replace(self.history_file)
        except Exception as e:
            logger.error(f"Failed to save history to {self.history_file}: {e}")

    def save(self, record: Dict[str, Any]) -> None:
        """
        Persists a screening result (valid or rejected) to history.json.
        """
        with self._lock:
            records = self._load_all()
            # Normalize ID keys
            screening_id = record.get("screening_id") or record.get("id")
            record["screening_id"] = screening_id
            
            # Prepend new record (most recent first)
            records.insert(0, record)
            # Limit retained records to 500 to keep JSON lightweight
            if len(records) > 500:
                records = records[:500]
            self._save_all(records)

    def get_all(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Returns paginated history records sorted newest first.
        """
        with self._lock:
            records = self._load_all()
            return records[:limit]

    def get_by_id(self, screening_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single screening record by screening_id.
        """
        with self._lock:
            records = self._load_all()
            for r in records:
                if r.get("screening_id") == screening_id or r.get("id") == screening_id:
                    return r
            return None

history_service = HistoryService()
