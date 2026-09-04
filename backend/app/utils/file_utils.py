import os
import uuid
from pathlib import Path
from typing import Tuple, Optional
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.core.logging_config import logger

def generate_unique_id() -> str:
    return str(uuid.uuid4())

def sanitize_filename(filename: Optional[str]) -> str:
    """
    Prevents path traversal attacks by extracting only the base name.
    """
    if not filename:
        return f"upload_{generate_unique_id()}.jpg"
    # Strip directory components
    safe_name = Path(filename).name
    # Strip dangerous characters
    clean_name = "".join(c for c in safe_name if c.isalnum() or c in "._- ")
    return clean_name or f"upload_{generate_unique_id()}.jpg"

def cleanup_file(path: Optional[str | Path]) -> None:
    """
    Safely deletes a temporary file if it exists.
    """
    if not path:
        return
    try:
        p = Path(path)
        if p.exists() and p.is_file():
            p.unlink()
    except Exception as e:
        logger.warning(f"Failed to cleanup temporary file {path}: {e}")

async def validate_and_save_upload(file: UploadFile) -> Tuple[str, Path, bytes]:
    """
    Performs file/security validation:
    1. Checks filename and extension against allowed extensions (.jpg, .jpeg, .png)
    2. Enforces non-empty content
    3. Enforces max upload size
    4. Writes to server-side temporary file with unique identifier
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "INVALID_FILE",
                "message": "No filename provided in upload request."
            }
        )
    
    # Check extension
    safe_name = sanitize_filename(file.filename)
    ext = f".{safe_name.split('.')[-1].lower()}" if "." in safe_name else ""
    allowed = settings.allowed_extension_list
    
    if ext not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "INVALID_FILE",
                "message": f"Unsupported file format '{ext}'. Allowed formats: {', '.join(allowed)}"
            }
        )
    
    # Read bytes
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "INVALID_FILE",
                "message": "Uploaded file is empty (0 bytes)."
            }
        )
    
    max_bytes = settings.effective_max_upload_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "INVALID_FILE",
                "message": f"File exceeds maximum allowed size of {settings.effective_max_upload_mb}MB."
            }
        )
    
    unique_id = generate_unique_id()
    settings.absolute_upload_dir.mkdir(parents=True, exist_ok=True)
    temp_filename = f"{unique_id}_{safe_name}"
    saved_path = settings.absolute_upload_dir / temp_filename
    
    with open(saved_path, "wb") as f:
        f.write(contents)
        
    return unique_id, saved_path, contents
