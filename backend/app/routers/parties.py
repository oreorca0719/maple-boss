from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from app.models.party import Party, PartyCreate
from app.services.party_service import PartyService
from app.services.user_service import UserService
from app.dependencies import get_party_service, get_user_service

router = APIRouter(prefix="/parties", tags=["parties"])


@router.post("", response_model=Party, status_code=status.HTTP_201_CREATED)
def create_party(
    payload: PartyCreate,
    created_by: str,
    svc: PartyService = Depends(get_party_service),
    user_svc: UserService = Depends(get_user_service),
):
    # 창성자 존재 확인
    if not user_svc.get(created_by):
        raise HTTPException(status_code=404, detail="Creator not found")

    # 멤버 중 가입된 유저만 동기화 대상으로 추출 (창성자·외부인 제외)
    registered_member_ids: list[str] = []
    for member in payload.members:
        if member.user_id == created_by:
            continue
        if member.is_external:
            continue
        if user_svc.get(member.user_id):
            registered_member_ids.append(member.user_id)

    try:
        return svc.create(payload, created_by, registered_member_ids)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/date/{scheduled_date}", response_model=list[Party])
def list_parties_by_date(
    scheduled_date: str,
    svc: PartyService = Depends(get_party_service),
):
    return svc.list_by_date(scheduled_date)


@router.get("/user/{user_id}", response_model=list[Party])
def list_parties_by_user(
    user_id: str,
    date_prefix: Optional[str] = None,
    svc: PartyService = Depends(get_party_service),
):
    """창성자이거나 파티원으로 참여한 모든 파티 반환"""
    return svc.list_by_user(user_id, date_prefix)


@router.delete("/{scheduled_date}/{sk}", status_code=status.HTTP_204_NO_CONTENT)
def delete_party(
    scheduled_date: str,
    sk: str,
    svc: PartyService = Depends(get_party_service),
):
    svc.delete(scheduled_date, sk)
