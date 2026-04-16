from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import get_settings
from app.models.user import User
from app.services.user_service import UserService
from app.dependencies import get_user_service
from app.utils.password import verify_password

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

router = APIRouter(prefix="/auth", tags=["auth"])


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


def create_access_token(user_id: str) -> str:
    settings = get_settings()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": user_id, "exp": expire},
        settings.app_secret_key,
        algorithm=ALGORITHM,
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    svc: UserService = Depends(get_user_service),
) -> User:
    exc = HTTPException(
        status_code=401,
        detail="인증 정보가 유효하지 않습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        settings = get_settings()
        payload = jwt.decode(token, settings.app_secret_key, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise exc
    except JWTError:
        raise exc

    user = svc.get(user_id)
    if not user:
        raise exc
    return user


@router.post("/login", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    svc: UserService = Depends(get_user_service),
):
    """
    username = 본캐 닉네임 (로그인 ID)
    password = 비밀번호
    """
    user = svc.get_full(form.username)
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="닉네임 또는 비밀번호가 올바르지 않습니다.")
    return Token(access_token=create_access_token(user.user_id))


@router.get("/me", response_model=User)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
