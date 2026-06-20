# app/routers/admin.py
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.database import SessionDep
from app.models import Users
from app.dependencies import get_current_user_from_token

router = APIRouter()

@router.get("/admin/get_user/{username}")
def get_user_by_username(
    username: str,
    session: SessionDep,
    current_user: Annotated[Users, Depends(get_current_user_from_token)],
):
    if current_user.rol != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    user_query = select(Users).where(Users.username == username)
    result = session.exec(user_query)
    user = result.first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

@router.get("/admin/disabled_users")
def get_disabled_users(
    session: SessionDep,
    current_user: Annotated[Users, Depends(get_current_user_from_token)],
):
    if current_user.rol != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    request = select(Users).where(Users.disable == True)
    result = session.exec(request)
    disabled_users = result.all()
    return disabled_users

@router.patch("/admin/enable_user/{username}")
def enable_user(
    username: str,
    session: SessionDep,
    current_user: Annotated[Users, Depends(get_current_user_from_token)],
):
    if current_user.rol != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    user_query = select(Users).where(Users.username == username)
    result = session.exec(user_query)
    user = result.first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.disable = False
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"message": f"Usuario {username} habilitado correctamente"}