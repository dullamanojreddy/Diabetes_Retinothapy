from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Explainable DR Screening API"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Model configuration
    MODEL_PATH: str = "models/best_efficientnet_b3.pth"
    REFERABLE_THRESHOLD: float = 0.13
    DEVICE: str = "auto"
    
    # Upload and storage limits
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: set[str] = {"png", "jpg", "jpeg", "webp"}
    
    # Storage paths (relative to backend folder)
    UPLOAD_DIR: str = "storage/uploads"
    RESULTS_DIR: str = "storage/results"
    HISTORY_DB_PATH: str = "storage/history.db"
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000"
    ]
    
    # Class mappings
    CLASS_MAPPING: dict[int, str] = {
        0: "No DR",
        1: "Mild DR",
        2: "Moderate DR",
        3: "Severe DR",
        4: "Proliferative DR"
    }

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow"
    )

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent

    @property
    def absolute_model_path(self) -> Path:
        p = Path(self.MODEL_PATH)
        return p if p.is_absolute() else self.base_dir / p

    @property
    def absolute_upload_dir(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        return p if p.is_absolute() else self.base_dir / p

    @property
    def absolute_results_dir(self) -> Path:
        p = Path(self.RESULTS_DIR)
        return p if p.is_absolute() else self.base_dir / p

    @property
    def absolute_history_db_path(self) -> Path:
        p = Path(self.HISTORY_DB_PATH)
        return p if p.is_absolute() else self.base_dir / p

settings = Settings()
