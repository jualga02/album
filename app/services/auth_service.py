# app/services/auth_service.py
from datetime import timedelta
from fastapi import HTTPException
from sqlmodel import select
from fastapi_mail import MessageSchema, MessageType
from jwt.exceptions import InvalidTokenError

from app.models import Users
from app.config import SECRET_KEY, ALGORITHM
from app.dependencies import create_access_token, get_password_hash
from app.services.email_service import fm


async def send_password_recovery_email(email: str, session) -> dict:
    """
    1. Busca el email.
    2. Si existe, genera un JWT de 30 min con propósito 'password_reset'.
    3. Envía un correo con el enlace al frontend.
    4. Siempre devuelve el mismo mensaje por seguridad (evita enumeración de emails).
    """
    success_message = {"message": "Si el correo está registrado, recibirás un enlace de recuperación."}
    
    user_query = select(Users).where(Users.email == email)
    user = session.exec(user_query).first()
    
    if not user:
        return success_message
    
    # Generar token con expiración de 30 minutos
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
        <p style="color: #7f8c8d; font-size: 12px; margin-top: 40px;">Si no solicitaste este cambio, ignora este correo. Tu contraseña actual seguirá siendo válida.</p>
    </body>
    </html>
    """
    
    message = MessageSchema(
        subject="Recuperación de contraseña - Álbum",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html
    )
    
    try:
        await fm.send_message(message)
        print(f"✅ Email de recuperación enviado a: {email}")
        return success_message
    except Exception as e:
        print(f"❌ Error enviando email de recuperación: {e}")
        return success_message


def validate_and_update_password(token: str, new_password: str, session) -> dict:
    """
    1. Valida el token JWT.
    2. Comprueba que el propósito sea 'password_reset'.
    3. Actualiza la contraseña en la base de datos.
    """
    import jwt
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("purpose") != "password_reset":
            raise HTTPException(status_code=400, detail="Token no válido para esta operación")
        
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Token inválido o corrupto")
        
        user_query = select(Users).where(Users.email == email)
        user = session.exec(user_query).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        user.hashed_password = get_password_hash(new_password)
        session.add(user)
        session.commit()
        session.refresh(user)
        
        return {"message": "Contraseña actualizada correctamente. Ya puedes iniciar sesión."}
        
    except InvalidTokenError:
        raise HTTPException(status_code=400, detail="El enlace ha expirado o no es válido. Solicita uno nuevo.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar la contraseña: {str(e)}")