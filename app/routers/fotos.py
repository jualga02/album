# app/routers/fotos.py
import shutil
from datetime import date
from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlmodel import select

from app.database import SessionDep
from app.models import Users, Foto
from app.schemas import FotoUpdate
from app.config import DOWNLOAD_DIR, UPLOAD_DIR_NAME
from app.dependencies import get_current_user_from_token

UPLOAD_DIR = Path(f"./{UPLOAD_DIR_NAME}")
UPLOAD_DIR.mkdir(exist_ok=True)

router = APIRouter()

@router.post("/new_foto/")
def create_foto(
    file: Annotated[UploadFile, File()],
    video: Annotated[bool, Form()],
    user_id: Annotated[str, Form()],
    session: SessionDep,
    current_user: Annotated[Users, Depends(get_current_user_from_token)],
    shot_date: Annotated[str | None, Form()] = None,
    comment: Annotated[str | None, Form()] = None,
    tag: Annotated[str | None, Form()] = None,
    title: Annotated[str | None, Form()] = None
):
    foto_query = select(Foto).where(Foto.file == file.filename)
    result = session.exec(foto_query)
    registry = result.first()

    user_query = select(Users).where(Users.id == user_id)
    user_result = session.exec(user_query)
    user = user_result.first()

    if current_user == user:
        if not registry:
            foto = Foto()
            foto.comment = comment
            foto.id = None
            foto.file = file.filename
            foto.title = title if title else foto.file
            foto.url = f"{DOWNLOAD_DIR}{foto.file}"
            foto.user_id = user_id
            foto.tag = tag
            foto.video = video
            if shot_date and shot_date.strip():
                foto.shot_date = date.fromisoformat(shot_date.strip())
            else:
                foto.shot_date = None

            file_path = UPLOAD_DIR / foto.file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            session.add(foto)
            session.commit()
            session.refresh(foto)
            return {
                "status": "success",
                "message": f"El archivo {file.filename} se ha guardado con éxito",
                "data": {
                    "id": foto.id,
                    "url": foto.url,
                    "file": foto.file,
                    "title": foto.title,
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El archivo {file.filename} ya se encuentra en la BBDD"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para subir fotos para este usuario"
        )

@router.get("/fotos/all")
def read_fotos(
    session: SessionDep,
    current_user: Annotated[Users, Depends(get_current_user_from_token)],
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Foto]:
    fotos = session.exec(select(Foto).offset(offset).limit(limit)).all()
    return fotos

@router.get("/fotos/only/{user}")
def read_fotos_by_user(
    session: SessionDep,
    current_user: Annotated[Users, Depends(get_current_user_from_token)],
    user: str,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Foto]:
    statement = (
        select(Foto)
        .join(Users, Foto.user_id == Users.id)
        .where(Users.username == user)
        .offset(offset)
        .limit(limit)
    )
    fotos = session.exec(statement).all()
    return fotos

@router.get("/fotos/search_title/{title_str}")
def search_fotos_by_title(
    session: SessionDep,
    current_user: Annotated[Users, Depends(get_current_user_from_token)],
    title_str: str,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100
) -> list[Foto]:
    statement = (
        select(Foto)
        .where(Foto.title.contains(title_str))
        .offset(offset)
        .limit(limit)
    )
    fotos = session.exec(statement).all()
    return fotos

@router.get("/fotos/search_tag/{tag_str}")
def search_fotos_by_tag(
    session: SessionDep,
    current_user: Annotated[Users, Depends(get_current_user_from_token)],
    tag_str: str,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100
) -> list[Foto]:
    statement = (
        select(Foto)
        .where(Foto.tag.contains(tag_str))
        .offset(offset)
        .limit(limit)
    )
    fotos = session.exec(statement).all()
    return fotos

@router.get("/fotos/{id}")
def read_foto(id: int, session: SessionDep) -> Foto:
    foto = session.get(Foto, id)
    if not foto:
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    return foto

@router.delete("/fotos/delete/{filename}")
async def delete_file(
    session: SessionDep,
    current_user: Annotated[Users, Depends(get_current_user_from_token)],
    filename: str
):
    foto_query = select(Foto).where(Foto.file == filename)
    result = session.exec(foto_query)
    registry = result.first()
    if not registry:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    if registry.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para borrar esta foto")

    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="El archivo físico no existe")

    try:
        file_path.unlink()
        session.delete(registry)
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error al borrar: {str(e)}")

    return {"message": f"Archivo '{filename}' borrado correctamente"}

@router.patch("/fotos/update/{filename}")
async def update_row_foto(
    session: SessionDep,
    current_user: Annotated[Users, Depends(get_current_user_from_token)],
    body: FotoUpdate,
    filename: str
):
    foto_query = select(Foto).where(Foto.file == filename)
    result = session.exec(foto_query)
    registry = result.first()

    user_query = select(Users).where(Users.id == registry.user_id)
    user_result = session.exec(user_query)
    user = user_result.first()

    if current_user == user:
        if not registry:
            raise HTTPException(status_code=404, detail="Foto no encontrada")
        foto = body.model_dump(exclude_unset=True)
        registry.sqlmodel_update(foto)
        session.add(registry)
        session.commit()
        session.refresh(registry)
        return registry
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar esta foto"
        )