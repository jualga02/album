import shutil

from fastapi import Depends, FastAPI, File, HTTPException, Path, Query, UploadFile
from typing import Annotated
from sqlmodel import Field, Session, SQLModel, create_engine, select
from pathlib import Path

app = FastAPI()

UPLOAD_DIR = Path("./fotos")
# UPLOAD_DIR.mkdir(exist_ok=True) crea la carpeta si no existe

# Clase de la tabla Foto
class Foto(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    file: str | None = Field(index=True)
    comment: str | None = Field(index=True)
    # route: str | None = Field(index=True)
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

# Subir un archivo
@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    #Construye la ruta con el nombre original del archivo
    file_path = UPLOAD_DIR / file.filename

    #Guarda el archivo en el disco
    with open(file_path, "wb") as buffer:
        #shutil copia eficientemente sin ocupar la RAM
        shutil.copyfileobj(file.file, buffer)
    return {"info": f"Fichero guardado en: {file_path}", "filename": file.filename}

# Borrar un archivo
@app.delete("/fotos/{filename}")
async def delete_file(filename: str):
    # Construïm la ruta completa del fitxer
    file_path = UPLOAD_DIR / filename
    
    # 1. Verifiquem si el fitxer existeix realment
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="El fitxer no existeix")
    
    try:
        # 2. Esborrem el fitxer de forma permanent
        file_path.unlink()
        return {"message": f"Fitxer '{filename}' esborrat correctament"}
    except Exception as e:
        # Per si hi ha problemes de permisos o el fitxer està en ús
        raise HTTPException(status_code=500, detail=f"Error al borrar: {str(e)}")