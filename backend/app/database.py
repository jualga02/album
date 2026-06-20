# backend/app/database.py
import os
from pathlib import Path
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy import text
from typing import Annotated
from fastapi import Depends

# ====== RUTA DE LA BASE DE DATOS ======
# Prioridad: variable de entorno > ruta por defecto
# - Desarrollo local: ../data/db/album.db
# - Docker producción: /app/data/db/album.db (montado desde disco local)
DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    str(Path(__file__).resolve().parent.parent / "data" / "db" / "album.db")
)

# Asegurar que el directorio existe
Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

sqlite_url = f"sqlite:///{DATABASE_PATH}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_username ON users (username)"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email ON users (email)"))