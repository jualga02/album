# app/services/user_service.py
from fastapi import HTTPException
from sqlmodel import select
from fastapi_mail import MessageSchema, MessageType

from app.models import Users
from app.services.email_service import fm


async def verify_user_account(username: str, email: str, session) -> Users:
    """
    1. Busca al usuario por username y email.
    2. Lo marca como verificado (isVerified=True).
    3. Envía un email al administrador para que active la cuenta.
    4. Devuelve el usuario actualizado.
    """
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
    
    return user