# app/routers/auth.py
from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.database import SessionDep
from app.models import Users
from app.schemas import Token, PasswordRecoverRequest, PasswordValidateRequest
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.dependencies import authenticate_user_by_email, create_access_token
from app.services.auth_service import send_password_recovery_email, validate_and_update_password

router = APIRouter()


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep
) -> Token:
    user = authenticate_user_by_email(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_logged=user.username or form_data.username,
        user_id=user.id
    )


@router.post("/token/pass/recover/")
async def recover_password(request: PasswordRecoverRequest, session: SessionDep):
    return await send_password_recovery_email(request.email, session)


@router.post("/token/pass/validate")
async def validate_password(request: PasswordValidateRequest, session: SessionDep):
    return validate_and_update_password(request.token, request.new_password, session)