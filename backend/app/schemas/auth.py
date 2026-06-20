from pydantic import BaseModel, EmailStr

class PasswordRecoverRequest(BaseModel):
    email: EmailStr

class PasswordValidateRequest(BaseModel):
    token: str
    new_password: str