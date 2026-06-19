# app/routers/users.py
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select
from sqlalchemy.exc import IntegrityError

from app.database import SessionDep
from app.models import Users, Usercreate
from app.schemas import UsersUpdate
from app.dependencies import get_password_hash, get_current_user_from_token
from app.services.email_service import send_welcome_email

router = APIRouter()

@router.post("/new_user/")
async def create_user(user: Usercreate, session: SessionDep):
    user_query = select(Users).where(
        (Users.username == user.username) | (Users.email == user.email)
    )
    result = session.exec(user_query)
    registry = result.first()
    if not registry:
        h_password = get_password_hash(user.password)
        extra_data = user.model_dump(exclude={"password"})
        db_user = Users(**extra_data, hashed_password=h_password)
        try:
            session.add(db_user)
            session.commit()
            session.refresh(db_user)
            email_sent = await send_welcome_email(
                user_email=db_user.email,
                username=db_user.username,
                full_name=db_user.full_name
            )
            return {
                "message": "Usuario creado correctamente",
                "name": db_user.full_name,
                "email_sent": email_sent
            }
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El username o el email ya existen en la BBDD"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El username o el email ya existen en la BBDD"
        )

@router.delete("/delete_user/{username}")
def delete_user(username: str, session: SessionDep):
    user_query = select(Users).where(Users.username == username)
    result = session.exec(user_query)
    registry = result.first()
    if not registry:
        return {"message": f"El usuario {username} no se encuentra en la BBDD"}
    else:
        session.delete(registry)
        session.commit()
        return {"message": f"El usuario {username} se ha borrado satisfactoriamente"}

@router.patch("/users/update/{username}")
async def update_user(
    session: SessionDep,
    current_user: Annotated[Users, Depends(get_current_user_from_token)],
    body: UsersUpdate,
    username: str
):
    users_query = select(Users).where(Users.username == username)
    result = session.exec(users_query)
    registry = result.first()
    
    if not registry:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if username != current_user.username:
        raise HTTPException(status_code=403, detail="No tienes permiso para actualizar este usuario")
    
    # Excluir password del update (por seguridad)
    user_data = body.model_dump(exclude_unset=True, exclude={"password"})
    registry.sqlmodel_update(user_data)
    session.add(registry)
    session.commit()
    session.refresh(registry)
    return registry

@router.get("/users/all")
def get_all_users(
    session: SessionDep,
    current_user: Annotated[Users, Depends(get_current_user_from_token)],
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Users]:
    photoUsers = session.exec(select(Users).offset(offset).limit(limit)).all()
    return photoUsers

@router.get("/users/me/items/")
async def read_own_items(
    session: SessionDep,
    current_user: Annotated[Users, Depends(get_current_user_from_token)]
):
    user_query = select(Users).where(Users.id == current_user.id)
    result = session.exec(user_query)
    registry = result.first()
    if not registry:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if registry.id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso")
    return current_user