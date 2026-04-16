from fastapi import APIRouter, Depends, HTTPException, status

from app.models.user import User, UserCreate, UserUpdate
from app.services.user_service import UserService
from app.services.character_service import CharacterService
from app.dependencies import get_user_service, get_character_service
from app.utils.password import hash_password

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, svc: UserService = Depends(get_user_service)):
    if svc.get(payload.user_id):
        raise HTTPException(status_code=409, detail="User already exists")
    payload.password_hash = hash_password(payload.password_hash)
    return svc.create(payload)


@router.get("", response_model=list[User])
def list_users(svc: UserService = Depends(get_user_service)):
    return svc.list_all()


@router.get("/{user_id}", response_model=User)
def get_user(user_id: str, svc: UserService = Depends(get_user_service)):
    user = svc.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=User)
def update_user(
    user_id: str,
    payload: UserUpdate,
    svc: UserService = Depends(get_user_service),
):
    updated = svc.update(user_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated


@router.get("/{user_id}/earnings-history", response_model=list[dict], tags=["earnings"])
def get_earnings_history(
    user_id: str,
    weeks: int = 8,
    char_svc: CharacterService = Depends(get_character_service),
):
    """유저의 최근 N주 수익 히스토리 (본캐+부캐 전체 합산, 차트용)"""
    return char_svc.get_weekly_earnings_history(user_id, weeks)
