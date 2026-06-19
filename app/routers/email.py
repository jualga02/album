# app/routers/email.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from fastapi_mail import MessageSchema, MessageType

from app.database import SessionDep
from app.services.email_service import fm
from app.services.user_service import verify_user_account

router = APIRouter()


@router.get("/verify-account", response_class=HTMLResponse)
async def verify_account(username: str, email: str, session: SessionDep):
    try:
        user = await verify_user_account(username, email, session)
        
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
        
    except HTTPException:
        raise
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