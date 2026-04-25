from fastapi import APIRouter

router = APIRouter()

# Ruta inicial
@router.get("/")
def read_root():
    return {"Hola":"desde nuestro Album"}