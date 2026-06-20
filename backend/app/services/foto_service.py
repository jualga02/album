# backend/app/services/foto_service.py
import os
import shutil
from datetime import date
from pathlib import Path
from fastapi import HTTPException

# ====== RUTA DE MEDIOS (fotos y videos juntos) ======
# Prioridad: variable de entorno > ruta por defecto
# - Desarrollo local: ../data/media
# - Docker producción: /mnt/raid5/Album (montado desde RAID 5)
MEDIA_PATH = os.getenv(
    "MEDIA_PATH",
    str(Path(__file__).resolve().parent.parent.parent / "data" / "media")
)

UPLOAD_DIR = Path(MEDIA_PATH)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def save_uploaded_file(file, filename: str) -> Path:
    """Guarda un archivo subido (foto o video) en el directorio de medios."""
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
    """Construye la URL pública de un archivo (foto o video)."""
    # En producción, esta URL la construirá el proxy inverso (Traefik)
    # Por ahora, usamos la URL relativa
    return f"/static/{filename}"


def parse_shot_date(shot_date_str: str | None) -> date | None:
    """Convierte un string de fecha a objeto date, o None si está vacío."""
    if shot_date_str and shot_date_str.strip():
        return date.fromisoformat(shot_date_str.strip())
    return None