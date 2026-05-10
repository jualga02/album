import shutil
import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from datetime import date, datetime, timedelta, timezone
from fastapi import Depends, FastAPI, File, Form, HTTPException, Path, Query, UploadFile, status
from typing import Annotated, Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Field, Session, SQLModel, create_engine, select
from pathlib import Path
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Usar Jinja2 como motor de plantillas

app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:4200"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
DOWNLOAD_DIR = "http://localhost:8000/static/"
UPLOAD_DIR = Path("./fotos")
# UPLOAD_DIR.mkdir(exist_ok=True) crea la carpeta si no existe

# Montar una carpeta para servir archivos estáticos
# Ahora puedes acceder a la foto en: /static/nombre_de_la_foto.jpg
app.mount("/static", StaticFiles(directory="fotos"), name="static")

    


#Clase Users. Implementa la seguridad.
'''Para que el campo contraseña no aparezca en la bbdd y el dato 'id' no 
   aparezca en los datos solicitados al usuario, es necesario crear tres clases,
   una común, otra para el usuario y una tercera para la bbdd.
   Aparte, para que la columna Id aparezca la primera, deberá procesarse en primer lugar.
'''
# Id como primer campo. Para que el campo 'id' aparezca el primero debe procesarse antes
class Userid(SQLModel):
    id: int | None = Field(default=None, primary_key=True)

# Base común
class Userbase(Userid):
    username: str | None = Field(index=True, unique=True)
    email: str | None
    full_name: str | None

# Datos del usuario
class Usercreate(Userbase):
    password: str | None

# Tabla para la bbdd
class Users(Userbase, table=True):    
    hashed_password: str | None = Field(index=True)
    disable: bool | None = Field(index=True, default=False)    
    rol: str | None = Field(default='user')

# Tabla para actualizaciones de usuario en la tabla Users
class UsersUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None    

# Clase de la tabla Foto
class Foto(SQLModel, table=True):
    #Este campo estará oculto al usuario en el frontend
    id: int | None = Field(default=None, primary_key=True)
    #Este campo debe ser oculto tambien y añadido de forma automática
    file: str | None = Field(index=True)
    #Oculto al usuario. Deberá reprogramarse en producción
    url: str | None
    comment: str | None 
    #Este campo estará oculto al usuario en el frontend
    user_id: int | None = Field(default=None, index=True, foreign_key="users.id")
    # up_date debe ser siempre null. La pondrá el sistema.
    #Este campo estará oculto al usuario en el frontend
    up_date: date | None = Field(default_factory=date.today, index=True)
    # shot_date puede ser 'null' o un tipo string fecha: "yyyy-mm-dd"
    shot_date: date | None = Field(default_factory=date.today, index=True)
    tag: str | None = Field(index=True)
    video: bool | None = Field(index=True)
    
# Clase para actualizaciones de usuario de la tabla Foto
class FotoUpdate(BaseModel):
    comment: Optional[str] = None
    shot_date: Optional[date] = None
    tag: Optional[str] = None
    video: Optional[bool] = False



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


# Ruta inicial
@app.get("/")
def read_root():
    return {"Hola":"desde nuestro Album"}

# ====================================================================
# Security
# ====================================================================
SECRET_KEY = "a2c315dfbbc06c5e8571a69e8ef67492860313627195b2e23c9eb0fd2f75d42b"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300

# Clase Token
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None    



# El manejador de Argon2 será 'password_hash'
password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummypassword")

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

# Esta función genera la contraseña 'hasheada'
def get_password_hash(password):    
    return password_hash.hash(password)


def get_user(session: SessionDep, username:str):
    user_query = select(Users).where(Users.username == username)
    user = session.exec(user_query).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


def authenticate_user(session: SessionDep, username: str, password: str ): 
    user = get_user(session, username)
    if not user:
        verify_password(password, DUMMY_HASH)
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})        
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate":"Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(session, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# MODIFICADO
async def get_current_active_user(current_user: Annotated[Users, Depends(get_current_user)],):
    if current_user.disable:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user



# Autentica a un usuario, el cual, debe haberse registrado previamente.
@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep) -> Token:
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")




# MODIFICADO. Devuelve el nombre del usuario registrado para mostrarlo en la web
@app.get("/users/me/")
async def read_users_me(current_user: Annotated[Users, Depends(get_current_active_user)],) -> Users:
    return current_user

# MODIFICADO. Devuelve todos los datos del usuario registrado para mostrar el perfil en la web
@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[Users, Depends(get_current_active_user)],):
    return [{"item_id": "Foo", "owner": current_user.username}]


# END SECURITY CODE ====================================================================


# RUTAS TABLA USERS ====================================================================

# Crear un nuevo usuario. 
@app.post("/new_user/")
def create_user(user: Usercreate, session: SessionDep):
    #Comprobamos que el nombre de usuario no exista en la BBDD
    user_query = select(Users).where(Users.username == user.username)
    result = session.exec(user_query)
    registry = result.first()
    if not registry:

        h_password = get_password_hash(user.password)

        extra_data = user.model_dump(exclude={"password"})
        db_user = Users(**extra_data, hashed_password=h_password)

        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return {"message": "usuario creado para ","name": db_user.full_name }
    
    else:
        return {"message": f"El usuario {user.username} ya existe en la BBDD"}

# Borrar un usuario. 
@app.delete("/delete_user/{username}")
def delete_user(username: str, session: SessionDep):
    user_query = select(Users).where(Users.username == username)
    result = session.exec(user_query)
    registry = result.first()
    if not registry:
         return {"message": f"El usuario {username} no se encuentra en la BBDD"}
    else:
        session.delete(registry)
        session.commit()
        return {"message": f"El usuario {username} se ha borrado satisfactoriamente"}
    
# Actualizar un usuario.
@app.patch("/users/update/{username}")
async def update_row(session: SessionDep, body: Userbase, username: str):
    users_query = select(Users).where(Users.username == username)
    result = session.exec(users_query)
    registry = result.first()
    if not registry:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    else:
        user = body.model_dump(exclude_unset=True)    
        registry.sqlmodel_update(user)

        session.add(registry)
        session.commit()
        session.refresh(registry)
        return registry

# FIN USERS ===============================================================================



# RUTAS TABLA FOTOS =======================================================================


# Crear una foto. 
@app.post("/new_foto/")
async def create_foto(
        shot_date: Annotated[str, Form()],
        comment: Annotated[str, Form()],
        tag: Annotated[str, Form()],
        file: Annotated[UploadFile, File()],
        video: Annotated[bool, Form()],
        session: SessionDep, 
    )-> dict | Foto:

    foto_query = select(Foto).where(Foto.file == file.filename)
    result = session.exec(foto_query)
    registry = result.first()
    if not registry:
        foto = Foto()
        foto.comment = comment
        foto.id = None
        foto.file = file.filename
        foto.url = f"{DOWNLOAD_DIR}{foto.file}"
        foto.user_id = 0
        # "2025-01-01"
        foto.shot_date =  shot_date         
        foto.tag = tag
        foto.video = video
        # Corrección del tipo Date para la BBDD
        if foto.shot_date != None:
            foto.shot_date = date.fromisoformat(foto.shot_date)

        # Subida del archivo
        #Construye la ruta con el nombre original del archivo
        file_path = UPLOAD_DIR / foto.file

        #Guarda el archivo en el disco
        with open(file_path, "wb") as buffer:
            #shutil copia eficientemente sin ocupar la RAM
            shutil.copyfileobj(file.file, buffer)
        #return {"info": f"Fichero guardado en: {file_path}", "filename": file.filename}

        # Añadido de datos a la BBDD
        session.add(foto)
        session.commit()
        session.refresh(foto)
        return foto
    else:
        return {"message": f"El archivo {file.filename} ya se encuentra en la BBDD"}




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


# Borrar un archivo. 
@app.delete("/fotos/{filename}")
async def delete_file(session: SessionDep, filename: str):
    # Borrado del registro en la BBDD
    foto_query = select(Foto).where(Foto.file == filename)
    result = session.exec(foto_query)
    registry = result.first()
    if not registry:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    session.delete(registry)
    session.commit()

    # Construïm la ruta completa del fitxer
    file_path = UPLOAD_DIR / filename
    
    # 1. Verifiquem si el fitxer existeix realment
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="El fitxer no existeix")
    
    try:
        # 2. Esborrem el fitxer de forma permanent
        file_path.unlink()
        
    except Exception as e:
        # Per si hi ha problemes de permisos o el fitxer està en ús
        raise HTTPException(status_code=500, detail=f"Error al borrar: {str(e)}")

    
    return {"message": f"Archivo '{filename}' borrado correctamente"}


# Actualizar una foto
@app.patch("/fotos/update/{filename}")
async def update_row_foto(session: SessionDep, body: FotoUpdate, filename: str):


    foto_query = select(Foto).where(Foto.file == filename)
    result = session.exec(foto_query)
    registry = result.first()
    if not registry:
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    else:
        foto = body.model_dump(exclude_unset=True)  
        registry.sqlmodel_update(foto)
        session.add(registry)
        session.commit()
        session.refresh(registry)
        return registry
    

# Actualizar un usuario
@app.patch("/users/update/{username}")
async def update_row_user(session: SessionDep, body: UsersUpdate, username:str):
    user_query = select(Users).where(Users.username == username)
    result = session.exec(user_query)
    registry = result.first()
    if not registry:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    else:
        user = body.model_dump(exclude_unset=True, exclude={"password"})
       # if body.password != None:
        #    h_password = get_password_hash(body.password)
         #   db_user = Users(**user, hashed_password=h_password)

        registry.sqlmodel_update(user)
        session.add(registry)
        session.commit()
        session.refresh(registry)
        return registry

# FIN FOTOS  ===============================================================================
 