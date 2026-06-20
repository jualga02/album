from datetime import date
from typing import Optional
from sqlmodel import Field, SQLModel

# Clase de la tabla Foto
class Foto(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    file: str | None = Field(index=True)
    title: str | None = Field(index=True)
    url: str | None
    comment: str | None
    user_id: int | None = Field(default=None, index=True, foreign_key="users.id")
    up_date: date | None = Field(default_factory=date.today, index=True)
    shot_date: Optional[date] = Field(default=None, nullable=True)
    tag: str | None = Field(index=True)
    video: bool | None = Field(index=True)