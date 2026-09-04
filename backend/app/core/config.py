from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Explainable DR Screening API"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    APP_ENV: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Model configuration
    MODEL_PATH: str = "models/best_efficientnet_b3.pth"
    MODEL_DEVICE: str = "auto"
    DEVICE: str = "auto"  # Backward compatibility
    MODEL_VERSION: str = "b3-aptos-epoch7"
    REFERABLE_THRESHOLD: float = 0.13
    REFERABLE_MIN_GRADE: int = 2
    
    # Upload and storage limits
    MAX_UPLOAD_MB: int = 10
    MAX_UPLOAD_SIZE_MB: int = 10  # Backward compatibility
    ALLOWED_IMAGE_EXTENSIONS: str = ".jpg,.jpeg,.png,.webp"
    ALLOWED_EXTENSIONS: set[str] = {"png", "jpg", "jpeg", "webp"}
    
    # Storage paths (relative to backend folder)
    STORAGE_DIR: str = "storage"
    UPLOAD_DIR: str = "storage/uploads"
    RESULT_DIR: str = "storage/results"
    RESULTS_DIR: str = "storage/results"  # Backward compatibility
    HISTORY_FILE: str = "storage/history.json"
    HISTORY_DB_PATH: str = "storage/history.db"  # Backward compatibility
    
    # Image Quality and Fundus Validation Gate Thresholds
    MIN_IMAGE_DIMENSION: int = 150
    MIN_BRIGHTNESS: float = 15.0
    MAX_BRIGHTNESS: float = 245.0
    MIN_CONTRAST: float = 12.0
    MIN_BLUR_SCORE: float = 8.0

    # Phase 3 Deterministic Quality Assessment Service Settings
    QUALITY_FOCUS_GOOD_MIN: float = 30.0
    QUALITY_FOCUS_BORDERLINE_MIN: float = 10.0
    QUALITY_CONTRAST_GOOD_MIN: float = 40.0
    QUALITY_CONTRAST_BORDERLINE_MIN: float = 20.0
    QUALITY_LUMINANCE_MIN_GOOD: float = 40.0
    QUALITY_LUMINANCE_MAX_GOOD: float = 180.0
    QUALITY_LUMINANCE_MIN_BORDERLINE: float = 25.0
    QUALITY_LUMINANCE_MAX_BORDERLINE: float = 215.0
    QUALITY_GLARE_MAX_GOOD: float = 0.03
    QUALITY_GLARE_MAX_BORDERLINE: float = 0.08
    QUALITY_FOV_MIN_GOOD: float = 0.40
    QUALITY_FOV_MIN_BORDERLINE: float = 0.25
    
    # CORS
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    LOG_LEVEL: str = "INFO"
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
    def absolute_storage_dir(self) -> Path:
        p = Path(self.STORAGE_DIR)
        return p if p.is_absolute() else self.base_dir / p

    @property
    def absolute_upload_dir(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        return p if p.is_absolute() else self.base_dir / p

    @property
    def absolute_results_dir(self) -> Path:
        p = Path(self.RESULT_DIR)
        return p if p.is_absolute() else self.base_dir / p

    @property
    def absolute_history_file(self) -> Path:
        p = Path(self.HISTORY_FILE)
        return p if p.is_absolute() else self.base_dir / p

    @property
    def absolute_history_db_path(self) -> Path:
        p = Path(self.HISTORY_DB_PATH)
        return p if p.is_absolute() else self.base_dir / p

    @property
    def effective_device(self) -> str:
        return self.MODEL_DEVICE if self.MODEL_DEVICE != "auto" else self.DEVICE

    @property
    def effective_max_upload_mb(self) -> int:
        return self.MAX_UPLOAD_MB or self.MAX_UPLOAD_SIZE_MB

    @property
    def allowed_extension_list(self) -> list[str]:
        exts = [e.strip().lower() for e in self.ALLOWED_IMAGE_EXTENSIONS.split(",") if e.strip()]
        cleaned = [e if e.startswith(".") else f".{e}" for e in exts]
        return cleaned

settings = Settings()

