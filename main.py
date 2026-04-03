from fastapi import Depends, FastAPI, HTTPException, Query
from typing import Annotated
from sqlmodel import Field, Session, SQLModel, create_engine, select

app = FastAPI()


# Clase de la tabla Foto
class Foto(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    file: str | None = Field(index=True)
    comment: str | None = Field(index=True)
    route: str | None = Field(index=True)
    user: str | None = Field(index=True)

# Motor del modelo
sqlite_file_name = "album.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

# Sesión
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# Creación de tablas y base de datos al arrancar
@app.on_event("startup")
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@app.get("/")
def read_root():
    return {"Hola":"desde nuestro Album"}

# Crear una entrada
@app.post("/fotos/")
def create_foto(foto: Foto, session: SessionDep) -> Foto:
    session.add(foto)
    session.commit()
    session.refresh(foto)
    return foto

# Devolver todos los registros
@app.get("/fotos/")
def read_fotos(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
)-> list[Foto]:
    fotos = session.exec(select(Foto).offset(offset).limit(limit)).all()
    return fotos

# Devolver un registro
@app.get("/fotos/{id}")
def read_foto(id: int, session: SessionDep) -> Foto:
    foto = session.get(Foto, id)
    if not foto:
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    return foto



