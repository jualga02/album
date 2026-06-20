# app/routers/fotos.py
from typing import Annotated
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlmodel import select

from app.database import SessionDep
from app.models import Users, Foto
from app.schemas import FotoUpdate
from app.dependencies import get_current_user_from_token
from app.services.foto_service import save_uploaded_file, delete_photo_file, build_foto_url, parse_shot_date

router = APIRouter()


@router.post("/new_foto")
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
    # Verificar que la foto no existe ya
    foto_query = select(Foto).where(Foto.file == file.filename)
    registry = session.exec(foto_query).first()
    if registry:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El archivo {file.filename} ya se encuentra en la BBDD"
        )
    
    # Verificar permisos
    user_query = select(Users).where(Users.id == user_id)
    user = session.exec(user_query).first()
    if current_user != user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para subir fotos para este usuario"
        )
    
    # Crear el registro
    foto = Foto(
        comment=comment,
        file=file.filename,
        title=title if title else file.filename,
        url=build_foto_url(file.filename),
        user_id=user_id,
        tag=tag,
        video=video,
        shot_date=parse_shot_date(shot_date)
    )
    
    # Guardar archivo físico
    save_uploaded_file(file, foto.file)
    
    # Guardar en BBDD
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


@router.get("/fotos/all")
def read_fotos(
    session: SessionDep,
    current_user: Annotated[Users, Depends(get_current_user_from_token)],
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Foto]:
    return session.exec(select(Foto).offset(offset).limit(limit)).all()


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
    return session.exec(statement).all()


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
    return session.exec(statement).all()


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
    return session.exec(statement).all()


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
    registry = session.exec(foto_query).first()
    
    if not registry:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    
    if registry.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para borrar esta foto")
    
    try:
        delete_photo_file(filename)
        session.delete(registry)
        session.commit()
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error al borrar: {str(e)}")
    
    return {"message": f"Archivo '{filename}' borrado correctamente"}


@router.patch("/fotos/update/{filename}")
async def update_foto(
    session: SessionDep,
    current_user: Annotated[Users, Depends(get_current_user_from_token)],
    body: FotoUpdate,
    filename: str
):
    foto_query = select(Foto).where(Foto.file == filename)
    registry = session.exec(foto_query).first()
    
    if not registry:
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    
    user_query = select(Users).where(Users.id == registry.user_id)
    user = session.exec(user_query).first()
    
    if current_user != user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar esta foto"
        )
    
    foto_data = body.model_dump(exclude_unset=True)
    registry.sqlmodel_update(foto_data)
    session.add(registry)
    session.commit()
    session.refresh(registry)
    return registry