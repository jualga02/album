# app/routers/auth.py
from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.database import SessionDep
from app.models import Users
from app.schemas import Token, PasswordRecoverRequest, PasswordValidateRequest
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.dependencies import (
    authenticate_user_by_email,
    create_access_token,
    get_password_hash,
)
from app.services.email_service import fm, templates

import jwt
from jwt.exceptions import InvalidTokenError
from sqlmodel import select
from fastapi_mail import MessageSchema, MessageType

router = APIRouter()

@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep
) -> Token:
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
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_logged=user.username or form_data.username,
        user_id=user.id
    )

@router.post("/token/pass/recover/")
async def send_email_for_password(request: PasswordRecoverRequest, session: SessionDep):
    user_query = select(Users).where(Users.email == request.email)
    user = session.exec(user_query).first()
    success_message = {"message": "Si el correo está registrado, recibirás un enlace de recuperación."}

    if not user:
        return success_message

    reset_token_expires = timedelta(minutes=30)
    reset_token = create_access_token(
        data={"sub": user.email, "purpose": "password_reset"},
        expires_delta=reset_token_expires
    )
    reset_link = f"http://localhost:4200/passrecover?token={reset_token}"

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
        <h2 style="color: #2c3e50;">🔒 Recuperación de Contraseña</h2>
        <p>Hola {user.full_name or user.username},</p>
        <p>Has solicitado restablecer tu contraseña en <strong>Álbum</strong>.</p>
        <p>Haz clic en el siguiente botón para crear una nueva contraseña:</p>
        <p style="margin: 30px 0;">
            <a href="{reset_link}" style="background-color: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Restablecer Contraseña</a>
        </p>
        <p style="color: #e74c3c; font-size: 14px;">⚠️ Este enlace expirará en 30 minutos por seguridad.</p>
    </body>
    </html>
    """

    message = MessageSchema(
        subject="Recuperación de contraseña - Álbum",
        recipients=[request.email],
        body=html_content,
        subtype=MessageType.html
    )

    try:
        await fm.send_message(message)
        print(f"✅ Email de recuperación enviado a: {request.email}")
        return success_message
    except Exception as e:
        print(f"❌ Error enviando email de recuperación: {e}")
        return success_message

@router.post("/token/pass/validate")
async def validate_pass_token(request: PasswordValidateRequest, session: SessionDep):
    try:
        payload = jwt.decode(request.token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("purpose") != "password_reset":
            raise HTTPException(status_code=400, detail="Token no válido para esta operación")
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Token inválido o corrupto")
        user_query = select(Users).where(Users.email == email)
        user = session.exec(user_query).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        user.hashed_password = get_password_hash(request.new_password)
        session.add(user)
        session.commit()
        session.refresh(user)
        return {"message": "Contraseña actualizada correctamente. Ya puedes iniciar sesión."}
    except InvalidTokenError:
        raise HTTPException(status_code=400, detail="El enlace ha expirado o no es válido. Solicita uno nuevo.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar la contraseña: {str(e)}")