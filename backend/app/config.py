from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr

# Configuración de seguridad JWT
SECRET_KEY = "a2c315dfbbc06c5e8571a69e8ef67492860313627195b2e23c9eb0fd2f75d42b"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300

# Configuración de directorios
DOWNLOAD_DIR = "http://localhost:8000/static/"
UPLOAD_DIR_NAME = "fotos"

# Configuración de CORS
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:8080",
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

# Configuración de email (lee del .env)
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
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()