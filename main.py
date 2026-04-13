import shutil
import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
from fastapi import Depends, FastAPI, File, HTTPException, Path, Query, UploadFile, status
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Field, Session, SQLModel, create_engine, select
from pathlib import Path
from pydantic import BaseModel



app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

UPLOAD_DIR = Path("./fotos")
# UPLOAD_DIR.mkdir(exist_ok=True) crea la carpeta si no existe


#Clase Users. Implementa la seguridad.
class Users(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str | None = Field(index=True)
    full_name: str | None = Field(index=True)
    email: str | None = Field(index=True)
    hashed_password: str | None = Field(index=True)
    # disable: bool | None = Field(index=True)



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


# ====================================================================
# Security
# ====================================================================
SECRET_KEY = "a2c315dfbbc06c5e8571a69e8ef67492860313627195b2e23c9eb0fd2f75d42b"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc",
        "disabled": False,
    },
}

# Clase Token
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None    



# Clase User 
class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disable: bool | None = None

class UserInDB(User):
    hashed_password: str    

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummypassword")

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

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




async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)],):
   # if current_user.disable:
    #    raise HTTPException(status_code=400, detail="Inactive user")
    return current_user




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





@app.get("/users/me/")
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)],) -> User:
    return current_user

@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],):
    return [{"item_id": "Foo", "owner": current_user.username}]


# END SECURITY CODE ====================================================================


# RUTAS TABLA USERS ====================================================================

# Crear una entrada
@app.post("/users/")
def create_user(user: Users, session: SessionDep) -> Users:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# Rutas tabla Fotos ________________________________________________________________
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


# Fin rutas tabla fotos____________________________________________________________


'''
#para debug
import debugpy
debugpy.listen(("0.0.0.0", 5678))
print("En espera del depurador en el puerto 5678...")
'''

'''def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)'''

'''def get_user(username:str, session: SessionDep):
    user = session.get(Users, username)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user'''


'''def authenticate_user(fake_db, username: str, password: str): ORIGINAL
    user = get_user(fake_db, username)
    if not user:
        verify_password(password, DUMMY_HASH)
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user
'''


'''@app.post("/token") ORIGINAL
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],) -> Token:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
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
'''