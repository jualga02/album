from datetime import date
from typing import Optional
from pydantic import BaseModel

# Clase para actualizaciones de foto
class FotoUpdate(BaseModel):
    title: Optional[str] = None
    comment: Optional[str] = None
    shot_date: Optional[date] = None
    tag: Optional[str] = None
    video: Optional[bool] = False