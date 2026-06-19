# 📸 Álbum API

API REST desarrollada con **FastAPI** para gestión de álbumes fotográficos con sistema de autenticación, verificación de email y panel de administración.

## 🚀 Características

- ✅ Autenticación JWT con OAuth2
- ✅ Registro de usuarios con verificación de email
- ✅ Sistema de recuperación de contraseña
- ✅ Subida y gestión de fotos/videos
- ✅ Panel de administración para activar usuarios
- ✅ Búsqueda por título y tags
- ✅ Envío de emails con plantillas HTML

## 📁 Estructura del proyecto

album/
├── app/
│ ├── config.py # Configuración (JWT, CORS, email)
│ ├── database.py # Conexión a SQLite
│ ├── dependencies.py # Funciones de autenticación
│ ├── models/ # Modelos SQLModel (tablas)
│ │ ├── user.py
│ │ └── foto.py
│ ├── schemas/ # Esquemas Pydantic (validación)
│ │ ├── user.py
│ │ ├── foto.py
│ │ ├── token.py
│ │ └── auth.py
│ ├── services/ # Lógica de negocio
│ │ ├── auth_service.py
│ │ ├── user_service.py
│ │ ├── foto_service.py
│ │ └── email_service.py
│ └── routers/ # Endpoints agrupados por dominio
│ ├── auth.py
│ ├── users.py
│ ├── fotos.py
│ ├── email.py
│ └── admin.py
├── templates/ # Plantillas Jinja2 para emails
├── fotos/ # Archivos subidos (no subido a Git)
├── main.py # Punto de entrada de la app
├── .env # Variables de entorno (NO subido a Git)
├── .env.example # Plantilla de variables de entorno
└── requirements.txt # Dependencias Python


## 🛠️ Instalación

### 1. Clonar el repositorio

```bash
git clone <tu-repo>
cd album

### 2. Crear el entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

### 3. Instalar dependencias
pip install -r requirements.txt

### 4. Configurar variables de entorno
cp .env.example .env
# Edita .env con tus credenciales de email

🚀 Ejecución
Desarrollo

uvicorn main:app --reload

La API estará disponible en http://localhost:8000

Producción

fastapi run

📚 Documentación de la API
Una vez arrancado el servidor, accede a:
Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
🔐 Endpoints principales
Autenticación
POST /token - Login
POST /token/pass/recover/ - Recuperar contraseña
POST /token/pass/validate - Validar token y cambiar contraseña
Usuarios
POST /new_user/ - Registrar usuario
GET /users/all - Listar usuarios
PATCH /users/update/{username} - Actualizar usuario
DELETE /delete_user/{username} - Borrar usuario
Fotos
POST /new_foto/ - Subir foto
GET /fotos/all - Listar todas las fotos
GET /fotos/only/{user} - Fotos de un usuario
GET /fotos/search_title/{title_str} - Buscar por título
GET /fotos/search_tag/{tag_str} - Buscar por tag
PATCH /fotos/update/{filename} - Actualizar foto
DELETE /fotos/delete/{filename} - Borrar foto
Administración
GET /admin/disabled_users - Usuarios pendientes de activar
PATCH /admin/enable_user/{username} - Activar usuario

📧 Configuración de email
El proyecto usa fastapi-mail para enviar emails. Configura las variables en .env:

MAIL_USERNAME=tu_email@gmail.com
MAIL_PASSWORD=tu_password_de_aplicacion
MAIL_FROM=tu_email@gmail.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com

Nota para Gmail: Necesitarás crear una contraseña de aplicación.

🧪 Testing
Puedes probar los endpoints desde:
Swagger UI: http://localhost:8000/docs
Postman/Thunder Client
Frontend Angular en http://localhost:4200
📝 Licencia
Este proyecto es de uso privado.
👤 Autor
Desarrollado por [Tu Nombre]