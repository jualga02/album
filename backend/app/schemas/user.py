from typing import Optional
from pydantic import BaseModel

# Tabla para actualizaciones de usuario
class UsersUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None