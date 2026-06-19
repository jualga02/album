# app/routers/email.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlmodel import select
from fastapi_mail import MessageSchema, MessageType

from app.database import SessionDep
from app.models import Users
from app.services.email_service import fm, templates

router = APIRouter()

@router.get("/verify-account", response_class=HTMLResponse)
async def verify_user_account(username: str, email: str, session: SessionDep):
    try:
        user_query = select(Users).where(Users.username == username, Users.email == email)
        result = session.exec(user_query)
        user = result.first()

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        user.isVerified = True
        session.add(user)
        session.commit()
        session.refresh(user)
        print(f"✅ Usuario {username} marcado como verificado (isVerified=True)")

        admin_email = "clinton002@msn.com"
        admin_subject = f"Nueva cuenta pendiente de activación: {user.full_name}"
        admin_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #2c3e50;">🔔 Nueva cuenta pendiente de activación</h2>
            <p>Un nuevo usuario ha verificado su cuenta y está esperando tu aprobación:</p>
            <table style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <tr><td style="font-weight: bold; padding: 8px 0;">Nombre completo:</td><td>{user.full_name}</td></tr>
                <tr><td style="font-weight: bold; padding: 8px 0;">Usuario:</td><td>{user.username}</td></tr>
                <tr><td style="font-weight: bold; padding: 8px 0;">Email:</td><td>{user.email}</td></tr>
            </table>
            <p><strong>Acción requerida:</strong> Accede al panel de administración y cambia el campo <code>disable</code> a <code>False</code> para activar esta cuenta.</p>
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

        html_response = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Cuenta Verificada - Álbum</title>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f6f8; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
                .card {{ background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); text-align: center; max-width: 500px; }}
                .icon {{ font-size: 64px; margin-bottom: 20px; }}
                h2 {{ color: #2c3e50; margin-bottom: 15px; }}
                .status {{ background-color: #fff8e1; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; text-align: left; border-radius: 6px; }}
                .btn {{ display: inline-block; margin-top: 20px; padding: 12px 30px; background-color: #3498db; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; }}
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
                        Hemos notificado al administrador. En cuanto revise y active tu cuenta, recibirás un correo de confirmación.
                    </p>
                </div>
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

@router.post("/send-email")
async def send_email():
    message = MessageSchema(
        subject="Prueba desde FastAPI y Angular",
        recipients=["clinton002@msn.com"],
        body="Este es un correo de prueba usando variables de entorno.",
        subtype=MessageType.plain
    )
    await fm.send_message(message)
    return {"message": "Correo enviado con éxito"}