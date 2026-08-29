import uuid
import shutil
from pathlib import Path
from fastapi import HTTPException, UploadFile, status
from app.core.config import settings

def generate_unique_id() -> str:
    return str(uuid.uuid4())

async def validate_and_save_upload(file: UploadFile) -> tuple[str, Path, bytes]:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided in upload."
        )
    
    ext = file.filename.split(".")[-1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{ext}'. Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )
    
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )
    
    unique_id = generate_unique_id()
    settings.absolute_upload_dir.mkdir(parents=True, exist_ok=True)
    saved_filename = f"{unique_id}_{file.filename}"
    saved_path = settings.absolute_upload_dir / saved_filename
    
    with open(saved_path, "wb") as f:
        f.write(contents)
        
    return unique_id, saved_path, contents
