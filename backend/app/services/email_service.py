# app/services/email_service.py
from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig
from fastapi.templating import Jinja2Templates
from app.config import settings

# Configuración de fastapi-mail
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

fm = FastMail(conf)
templates = Jinja2Templates(directory="templates")

async def send_welcome_email(user_email: str, username: str, full_name: str):
    """Envía un email de bienvenida al nuevo usuario (sin adjuntos)."""
    try:
        validation_url = "http://localhost:8000/verify-account"
        html_content = templates.get_template("email_bienvenida.html").render({
            "username": username,
            "full_name": full_name,
            "user_email": user_email,
            "validation_url": validation_url
        })
        
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