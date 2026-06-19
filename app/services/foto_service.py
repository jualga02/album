# app/services/foto_service.py
import shutil
from datetime import date
from pathlib import Path
from fastapi import HTTPException

from app.config import DOWNLOAD_DIR, UPLOAD_DIR_NAME

UPLOAD_DIR = Path(f"./{UPLOAD_DIR_NAME}")
UPLOAD_DIR.mkdir(exist_ok=True)


def save_uploaded_file(file, filename: str) -> Path:
    """Guarda un archivo subido en el directorio de uploads."""
    file_path = UPLOAD_DIR / filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return file_path


def delete_photo_file(filename: str) -> None:
    """Borra un archivo físico del disco."""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="El archivo físico no existe")
    file_path.unlink()


def build_foto_url(filename: str) -> str:
    """Construye la URL pública de una foto."""
    return f"{DOWNLOAD_DIR}{filename}"


def parse_shot_date(shot_date_str: str | None) -> date | None:
    """Convierte un string de fecha a objeto date, o None si está vacío."""
    if shot_date_str and shot_date_str.strip():
        return date.fromisoformat(shot_date_str.strip())
    return None