# main.py
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import origins, UPLOAD_DIR_NAME
from app.database import create_db_and_tables
from app.routers import auth, users, fotos, email, admin

# ====== Crear la app ======
app = FastAPI(title="Álbum API")

# ====== CORS ======
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https?://(localhost|127.0.0.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== Archivos estáticos ======
UPLOAD_DIR = Path(f"./{UPLOAD_DIR_NAME}")
UPLOAD_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=UPLOAD_DIR_NAME), name="static")

# ====== Incluir routers ======
app.include_router(auth.router, tags=["Auth"])
app.include_router(users.router, tags=["Users"])
app.include_router(fotos.router, tags=["Fotos"])
app.include_router(email.router, tags=["Email"])
app.include_router(admin.router, tags=["Admin"])

# ====== Startup ======
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# ====== Ruta raíz ======
@app.get("/")
def read_root():
    return {"Hola": "desde nuestro Álbum"}