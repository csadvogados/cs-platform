from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.user import UserRead
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/token", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if not user or not verify_password(form.password, user.password_hash) or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos", headers={"WWW-Authenticate":"Bearer"})
    token = create_access_token(str(user.id), {"org": str(user.organization_id), "role": user.role})
    return Token(access_token=token)

@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    return user
