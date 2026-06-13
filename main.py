import shutil
import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from datetime import date, datetime, timedelta, timezone
from fastapi import Depends, FastAPI, File, Form, HTTPException, Path, Query, UploadFile, status
from typing import Annotated, Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlmodel import Field, Session, SQLModel, create_engine, select
from pathlib import Path
from pydantic import BaseModel, EmailStr
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig
from fastapi.templating import Jinja2Templates
from email.mime.image import MIMEImage
import traceback   
from fastapi.responses import HTMLResponse 

# Usar Jinja2 como motor de plantillas

app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:8080",
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
DOWNLOAD_DIR = "http://localhost:8000/static/"
UPLOAD_DIR = Path("./fotos")
# UPLOAD_DIR.mkdir(exist_ok=True) crea la carpeta si no existe
security = HTTPBearer()

# Montar una carpeta para servir archivos estáticos
# Ahora puedes acceder a la foto en: /static/nombre_de_la_foto.jpg
app.mount("/static", StaticFiles(directory="fotos"), name="static")

#=================> CONFIGURACIÓN DE FASTAPI-MAIL <=================

# 1. Definir el modelo de configuración que lee el archivo .env
class Settings(BaseSettings):
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    USE_CREDENTIALS: bool
    MAIL_FROM_NAME: str

    # Indicar a Pydantic que busque el archivo .env
    model_config = SettingsConfigDict(env_file=".env")

# 2. Cargar las variables de entorno
settings = Settings()

# 3. Pasar las variables a la configuración de fastapi-mail
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,           # Usar TLS para puerto 587
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# 4. Instanciar FastMail
fm = FastMail(conf)  

templates = Jinja2Templates(directory="templates")
#=================> FIN CONFIGURACIÓN DE FASTAPI-MAIL <=================

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
    email: str | None = Field(index=True, unique=True)
    full_name: str | None

# Datos del usuario
class Usercreate(Userbase):
    password: str | None

# Tabla para la bbdd
class Users(Userbase, table=True):    
    hashed_password: str | None = Field(index=True)
    disable: bool | None = Field(index=True, default=True)    
    isVerified: bool | None = Field(index=True, default=False)
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
    #Este campo debe ser añadido de forma automática
    file: str | None = Field(index=True)
    #Alias para 'file' que se mostrará al usuario en el frontend como opcional. Por defecto será el mismo valor que 'file'
    title: str | None = Field(index=True)
    #Oculto al usuario. Deberá reprogramarse en producción
    url: str | None
    comment: str | None 
    #Este campo estará oculto al usuario en el frontend
    user_id: int | None = Field(default=None, index=True, foreign_key="users.id")
    # up_date debe ser siempre null. La pondrá el sistema.
    #Este campo estará oculto al usuario en el frontend
    up_date: date | None = Field(default_factory=date.today, index=True)
    # shot_date puede ser 'null' o un tipo string fecha: "yyyy-mm-dd"
    # registro inicial (hasta 04-06-2026)
    #shot_date: date | None = Field(default_factory=date.today, index=True)
    shot_date: Optional[date] = Field(default=None, nullable=True)
    tag: str | None = Field(index=True)
    video: bool | None = Field(index=True)
    
# Clase para actualizaciones de usuario de la tabla Foto
class FotoUpdate(BaseModel):
    title: Optional[str] = None
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
    with engine.begin() as connection:
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_username ON users (username)"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email ON users (email)"))


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
    user_logged: str
    user_id: int

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


def authenticate_user_by_email(session: SessionDep, email: str, password: str):
    user_query = select(Users).where(Users.email == email)
    user = session.exec(user_query).first()
    
    if not user:
        verify_password(password, DUMMY_HASH)
        return False
    
    if not verify_password(password, user.hashed_password):
        return False
    
    # NUEVA VALIDACIÓN: Comprobar que el usuario está verificado Y activado
    if not user.isVerified:
        print(f"⚠️ Usuario {email} no ha verificado su cuenta aún")
        return False
    
    if user.disable:
        print(f"⚠️ Usuario {email} no ha sido habilitado todavía por el administrador")
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



# Autentica a un usuario, el cual, debe haberse registrado previamente, verifcado su email
# y ser habilitada su cuenta por el administrador (disabled = 0).
@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep) -> Token:
    user = authenticate_user_by_email(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer",user_logged=user.username or form_data.username, user_id=user.id)







# END SECURITY CODE ====================================================================
# =========================< ENVÍO DE EMAILS >===============================================

#import traceback # Asegúrate de tener este import al inicio del archivo si no lo tienes

async def send_welcome_email(user_email: str, username: str, full_name: str):
    """Envía un email de bienvenida al nuevo usuario (sin adjuntos)."""
    try:
        validation_url = "http://localhost:8000/verify-account"
        
        # Renderizar plantilla HTML
        html_content = templates.get_template("email_bienvenida.html").render({
            "username": username,
            "full_name": full_name,
            "user_email": user_email,
            "validation_url": validation_url
        })
        
        # Crear el mensaje SIN el parámetro 'attachments'
        message = MessageSchema(
            subject="¡Bienvenido/a a Álbum! - Tu cuenta ha sido creada",
            recipients=[user_email],
            body=html_content,
            subtype=MessageType.html
        )
        
        await fm.send_message(message)
        print(f"✅ EMAIL ENVIADO EXITOSAMENTE a: {user_email}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO al enviar email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    



@app.get("/verify-account", response_class=HTMLResponse)
async def verify_user_account(username: str, email: str, session: SessionDep):
    """
    Ruta activada por el botón 'Validar mi cuenta' del email de bienvenida.
    1. Marca al usuario como verificado (isVerified = True)
    2. Envía un email al administrador para que active la cuenta manualmente
    """
    try:
        # Buscar al usuario
        user_query = select(Users).where(Users.username == username, Users.email == email)
        result = session.exec(user_query)
        user = result.first()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Marcar como verificado
        user.isVerified = True
        session.add(user)
        session.commit()
        session.refresh(user)
        print(f"✅ Usuario {username} marcado como verificado (isVerified=True)")
        
        # Enviar email al administrador
        admin_email = "clinton002@msn.com"
        admin_subject = f"Nueva cuenta pendiente de activación: {user.full_name}"
        admin_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #2c3e50;">🔔 Nueva cuenta pendiente de activación</h2>
            <p>Un nuevo usuario ha verificado su cuenta y está esperando tu aprobación:</p>
            
            <table style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <tr>
                    <td style="font-weight: bold; padding: 8px 0;">Nombre completo:</td>
                    <td style="padding: 8px 0;">{user.full_name}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; padding: 8px 0;">Usuario:</td>
                    <td style="padding: 8px 0;">{user.username}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; padding: 8px 0;">Email:</td>
                    <td style="padding: 8px 0;">{user.email}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; padding: 8px 0;">Estado actual:</td>
                    <td style="padding: 8px 0; color: #f59e0b;">⚠️ Desactivado (disable=True)</td>
                </tr>
            </table>
            
            <p><strong>Acción requerida:</strong> Accede al panel de administración y cambia el campo <code>disable</code> a <code>False</code> para activar esta cuenta.</p>
            
            <hr style="border: none; border-top: 1px solid #e9ecef; margin: 30px 0;">
            <p style="color: #6c757d; font-size: 12px;">
                Este es un mensaje automático del sistema Álbum.
            </p>
        </body>
        </html>
        """
        
        message = MessageSchema(
            subject=admin_subject,
            recipients=[admin_email],
            body=admin_body,
            subtype=MessageType.html
        )
        
        await fm.send_message(message)
        print(f"✅ Email de notificación enviado al administrador: {admin_email}")
        
        # Devolver página HTML amigable al usuario
        html_response = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Cuenta Verificada - Álbum</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f6f8;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .card {{
                    background: white;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    text-align: center;
                    max-width: 500px;
                }}
                .icon {{
                    font-size: 64px;
                    margin-bottom: 20px;
                }}
                h2 {{
                    color: #2c3e50;
                    margin-bottom: 15px;
                }}
                p {{
                    color: #555;
                    line-height: 1.6;
                    margin-bottom: 20px;
                }}
                .status {{
                    background-color: #fff8e1;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                    text-align: left;
                    border-radius: 6px;
                }}
                .btn {{
                    display: inline-block;
                    margin-top: 20px;
                    padding: 12px 30px;
                    background-color: #3498db;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="icon">✅</div>
                <h2>¡Cuenta Verificada!</h2>
                <p>Hola <strong>{user.full_name or username}</strong>,</p>
                <p>Tu identidad ha sido confirmada correctamente.</p>
                
                <div class="status">
                    <p style="margin: 0; color: #856404;">
                        <strong>⚠️ Pendiente de activación final</strong><br>
                        Hemos notificado al administrador. En cuanto revise y active tu cuenta, 
                        recibirás un correo de confirmación y ya podrás iniciar sesión.
                    </p>
                </div>
                
                <p style="font-size: 14px; color: #6c757d;">
                    Usuario: <strong>{username}</strong><br>
                    Email: <strong>{email}</strong>
                </p>
                
                <a href="http://localhost:4200" class="btn">Volver a la aplicación</a>
            </div>
        </body>
        </html>
        """
        
        return html_response
        
    except Exception as e:
        print(f"❌ Error al verificar cuenta: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al verificar la cuenta: {str(e)}")


# RUTAS TABLA USERS ====================================================================
'''def get_current_user_from_token(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    token = credentials.credentials
    # AQUÍ DEBES VALIDAR TU JWT TOKEN (ej. con python-jose o PyJWT)
    # Si el token no es válido, lanza una excepción:
    # raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    return token # O retorna los datos del usuario decodificados'''

def get_current_user_from_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: SessionDep # Necesitamos la sesión para buscar en la BBDD
):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 1. Decodificamos el token JWT usando tu SECRET_KEY y ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    # 2. Buscamos al usuario en la base de datos
    user_query = select(Users).where(Users.username == username)
    user = session.exec(user_query).first()

    if user is None:
        raise credentials_exception
        
    # 3. ¡CLAVE! Devolvemos el objeto Users completo, no el string
    return user


# Crear un nuevo usuario. 
@app.post("/new_user/")
async def create_user(user: Usercreate, session: SessionDep):
    # Comprobamos que el usuario no exista
    user_query = select(Users).where(
        (Users.username == user.username) | (Users.email == user.email)
    )
    result = session.exec(user_query)
    registry = result.first()
    
    if not registry:
        h_password = get_password_hash(user.password)
        extra_data = user.model_dump(exclude={"password"})
        db_user = Users(**extra_data, hashed_password=h_password)
        
        try:
            session.add(db_user)
            session.commit()
            session.refresh(db_user)
            
            # ====== NUEVO: ENVIAR EMAIL ======
            email_sent = await send_welcome_email(
                user_email=db_user.email,
                username=db_user.username,
                full_name=db_user.full_name
            )
            
            return {
                "message": "Usuario creado correctamente",
                "name": db_user.full_name,
                "email_sent": email_sent
            }
            
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El username o el email ya existen en la BBDD"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El username o el email ya existen en la BBDD"
        )

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
async def update_row(session: SessionDep, body: UsersUpdate, username: str):
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

# Obtener todos los usuarios.
@app.get("/users/all")
def read_fotos(
    session: SessionDep,
    token: Annotated[str, Depends(get_current_user_from_token)],
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
)-> list[Users]:
    photoUsers= session.exec(select(Users).offset(offset).limit(limit)).all()
    return photoUsers


# MODIFICADO. Devuelve el nombre del usuario registrado para mostrarlo en la web
'''@app.get("/users/me/")
async def read_users_me(current_user: Annotated[Users, Depends(get_current_active_user)],) -> Users:
    return current_user'''

# MODIFICADO. Devuelve todos los datos del usuario registrado para mostrar el perfil en la web
@app.get("/users/me/items/")
async def read_own_items(
    session: SessionDep,
    current_user: Annotated[Users, Depends(get_current_user_from_token)]
):
    user_query = select(Users).where(Users.id == current_user.id)
    result = session.exec(user_query)
    registry = result.first()

    if not registry:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # 2. Control de propiedad (¡Crucial para la seguridad!)
    # Evita que un usuario autenticado borre fotos de otro usuario
    if registry.id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para borrar esta foto")
    
    return current_user

# FIN USERS ===============================================================================



# RUTAS TABLA FOTOS =======================================================================




# Crear una foto. 
@app.post("/new_foto/")
def create_foto(
          
        file: Annotated[UploadFile, File()],
        video: Annotated[bool, Form()],
        user_id: Annotated[str, Form()],
        session: SessionDep, 
        token: Annotated[str, Depends(get_current_user_from_token)],
        shot_date: Annotated[str | None, Form()] = None,
        comment:  Annotated[str | None, Form()] = None,
        tag: Annotated[str | None, Form()] = None,
        title: Annotated[str | None, Form()] = None
    ):

    foto_query = select(Foto).where(Foto.file == file.filename)
    result = session.exec(foto_query)
    registry = result.first()
    if not registry:
        foto = Foto()
        foto.comment = comment        
        foto.id = None
        foto.file = file.filename
        foto.title = title if title else foto.file
        foto.url = f"{DOWNLOAD_DIR}{foto.file}"
        foto.user_id = user_id
        foto.tag = tag
        foto.video = video
        # "2025-01-01"
        #foto.shot_date =  shot_date      
        if shot_date and shot_date.strip():
            foto.shot_date = date.fromisoformat(shot_date.strip())
        else:
            foto.shot_date = None
        
        # Corrección del tipo Date para la BBDD
        #if foto.shot_date != None:
        #   foto.shot_date = date.fromisoformat(foto.shot_date)

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
        # RETORNO EXITOSO: Enviamos un mensaje explícito legible por el Frontend
        return {
            "status": "success",
            "message": f"El archivo {file.filename} se ha guardado con éxito",
            "data": {
                "id": foto.id,
                "url": foto.url,
                "file": foto.file,
                "title": foto.title,
            }
        }
    else:
        #Respuesta inicial
        #return {"message": f"El archivo {file.filename} ya se encuentra en la BBDD"}
        #Respuesta recomendada
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El archivo {file.filename} ya se encuentra en la BBDD"
        )




# Devolver todos los registros
@app.get("/fotos/all")
def read_fotos(
    session: SessionDep,
    token: Annotated[str, Depends(get_current_user_from_token)],
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
)-> list[Foto]:
    fotos = session.exec(select(Foto).offset(offset).limit(limit)).all()
    return fotos

# Devolver todos los registros de un usuario
@app.get("/fotos/only/{user}")
def read_fotos(
    session: SessionDep,
    token: Annotated[str, Depends(get_current_user_from_token)],
    user: str,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
)-> list[Foto]:
    statement = (
        select(Foto)
        .join(Users, Foto.user_id == Users.id)
        .where(Users.username == user)
        .offset(offset)
        .limit(limit)
    )
    fotos = session.exec(statement).all()
    return fotos

# Devolver un registro
@app.get("/fotos/{id}")
def read_foto(id: int, session: SessionDep) -> Foto:
    foto = session.get(Foto, id)
    if not foto:
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    return foto

# Devolver todos los registros que contengan una cadena específica en el campo 'title'
@app.get("/fotos/search_title/{title_str}")
def search_fotos_by_title(
    session: SessionDep,
    token: Annotated[str, Depends(get_current_user_from_token)],
    title_str: str,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100
) -> list[Foto]:
    statement = (
        select(Foto)
        .where(Foto.title.contains(title_str))
        .offset(offset)
        .limit(limit)
    )
    fotos = session.exec(statement).all()
    return fotos

# Devolver todos los registros que contengan una cadena específica en el campo 'tag'
@app.get("/fotos/search_tag/{tag_str}")
def search_fotos_by_tag(
    session: SessionDep,
    token: Annotated[str, Depends(get_current_user_from_token)],
    tag_str: str,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100
) -> list[Foto]:
    statement = (
        select(Foto)
        .where(Foto.tag.contains(tag_str))
        .offset(offset)
        .limit(limit)
    )
    fotos = session.exec(statement).all()
    return fotos

# Borrar un archivo. 
'''@app.delete("/fotos/delete/{filename}")
async def delete_file(
    session: SessionDep, 
    current_user: Annotated[User, Depends(get_current_user_from_token)], 
    filename: str
    ):
    # Borrado del registro en la BBDD
    foto_query = select(Foto).where(Foto.file == filename)
    result = session.exec(foto_query)
    registry = result.first()
    if not registry:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    session.delete(registry)
    session.commit()

    # Construimos la ruta del archivo a borrar
    file_path = UPLOAD_DIR / filename
    
    # Verificamos si el archivo existe antes de borrarlo
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="El archivo no existe")
    
    try:
        # 2. Esborrem el fitxer de forma permanent
        file_path.unlink()
        
    except Exception as e:
        # Por si hay problemas de permisos o el archivo está siendo usado por otro proceso, etc.
        raise HTTPException(status_code=500, detail=f"Error al borrar: {str(e)}")

    
    return {"message": f"Archivo '{filename}' borrado correctamente"}'''

# Borrar un archivo. 
@app.delete("/fotos/delete/{filename}")
async def delete_file(
    session: SessionDep, 
    # 1. Cambiamos 'str' por el modelo de tu usuario (ej. User) que devuelve tu dependencia
    current_user: Annotated[Users, Depends(get_current_user_from_token)], 
    filename: str
):
    # Selección del registro en la BBDD
    foto_query = select(Foto).where(Foto.file == filename)
    result = session.exec(foto_query)
    registry = result.first()
    
    if not registry:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
        
    # 2. Control de propiedad (¡Crucial para la seguridad!)
    # Evita que un usuario autenticado borre fotos de otro usuario
    if registry.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para borrar esta foto")

    # Construimos la ruta del archivo a borrar
    file_path = UPLOAD_DIR / filename
    
    # Verificamos si el archivo existe antes de borrarlo de la BBDD
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="El archivo físico no existe")
    
    try:
        # Borramos el fichero físico primero
        file_path.unlink()
        
        # Si el archivo se borra bien, confirmamos el borrado en la BBDD
        session.delete(registry)
        session.commit()
        
    except Exception as e:
        session.rollback()  # Deshace cambios si algo falla
        raise HTTPException(status_code=500, detail=f"Error al borrar: {str(e)}")
    
    return {"message": f"Archivo '{filename}' borrado correctamente"}


# Actualizar una foto
@app.patch("/fotos/update/{filename}")
async def update_row_foto(
    session: SessionDep, 
    token: Annotated[str, Depends(get_current_user_from_token)], 
    body: FotoUpdate, 
    filename: str
    ):


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
async def update_row_user(
    session: SessionDep, 
    current_user: Annotated[Users, Depends(get_current_user_from_token)],
    body: UsersUpdate, 
    username:str
):
    user_query = select(Users).where(Users.username == username)
    result = session.exec(user_query)
    registry = result.first()
    if not registry:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    else:
        if registry.id != current_user.id:
            raise HTTPException(status_code=403, detail="No tienes permiso para actualizar este usuario")
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
 
# RUTAS DE ENVÍO DE CORREOS CON FASTAPI-MAIL ==================================================
# Ejemplo de endpoint para enviar un correo
@app.post("/send-email")
async def send_email():
    message = MessageSchema(
        subject="Prueba desde FastAPI y Angular",
        recipients=["clinton002@msn.com"],
        body="Este es un correo de prueba usando variables de entorno.",
        subtype=MessageType.plain
    )
    await fm.send_message(message)
    return {"message": "Correo enviado con éxito"}