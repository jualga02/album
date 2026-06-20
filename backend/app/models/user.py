from sqlmodel import Field, SQLModel

# Id como primer campo
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