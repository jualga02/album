from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy import text
from typing import Annotated
from fastapi import Depends

# Configuración de la base de datos
sqlite_file_name = "album.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

# Dependencia de sesión
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# Creación de tablas
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_username ON users (username)"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email ON users (email)"))