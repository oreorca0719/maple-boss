from fastapi import APIRouter, Depends, HTTPException, status

from app.models.character import Character, CharacterCreate, BossChecklist
from app.services.character_service import CharacterService
from app.services.party_service import PartyService
from app.services.user_service import UserService
from app.external.nexon_api import NexonApiClient
from app.dependencies import get_character_service, get_party_service, get_user_service, get_nexon_client

router = APIRouter(prefix="/users/{user_id}/characters", tags=["characters"])


@router.post("", response_model=Character, status_code=status.HTTP_201_CREATED)
async def register_character(
    user_id: str,
    payload: CharacterCreate,
    char_svc: CharacterService = Depends(get_character_service),
    nexon: NexonApiClient = Depends(get_nexon_client),
):
    """캐릭터 등록 + 넥슨 API에서 기본 정보 즉시 동기화"""
    payload.user_id = user_id
    char = char_svc.create(payload)

    # 넥슨 API 동기화 (실패해도 등록은 완료된 상태로 반환)
    api_data = await nexon.fetch_character(payload.char_name)
    if api_data:
        from app.models.character import CharacterUpdate
        char = char_svc.sync_from_api(user_id, payload.char_name, api_data) or char

    return char


@router.get("", response_model=list[Character])
def list_characters(
    user_id: str,
    char_svc: CharacterService = Depends(get_character_service),
):
    return char_svc.list_by_user(user_id)


@router.get("/{char_name}", response_model=Character)
def get_character(
    user_id: str,
    char_name: str,
    char_svc: CharacterService = Depends(get_character_service),
):
    char = char_svc.get(user_id, char_name)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    return char


@router.post("/{char_name}/sync", response_model=Character)
async def sync_character(
    user_id: str,
    char_name: str,
    char_svc: CharacterService = Depends(get_character_service),
    nexon: NexonApiClient = Depends(get_nexon_client),
):
    """넥슨 API에서 캐릭터 정보 수동 갱신"""
    api_data = await nexon.fetch_character(char_name)
    if not api_data:
        raise HTTPException(status_code=502, detail="Failed to fetch from Nexon API")
    updated = char_svc.sync_from_api(user_id, char_name, api_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Character not found")
    return updated


@router.delete("/{char_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_character(
    user_id: str,
    char_name: str,
    char_svc: CharacterService = Depends(get_character_service),
    party_svc: PartyService = Depends(get_party_service),
):
    char_svc._party_service = party_svc
    char_svc.delete(user_id, char_name)


# ------------------------------------------------------------------
# 보스 체크리스트
# ------------------------------------------------------------------

@router.put("/{char_name}/checklist", response_model=BossChecklist)
def save_checklist(
    user_id: str,
    char_name: str,
    checklist: BossChecklist,
    char_svc: CharacterService = Depends(get_character_service),
    user_svc: UserService = Depends(get_user_service),
):
    """
    보스 체크리스트 저장.
    is_cleared=True인 보스들의 수익을 합산하여 유저 누적 수익에 반영.
    """
    checklist.user_id = user_id
    checklist.char_name = char_name
    saved, week_total, month_total = char_svc.save_checklist(checklist)
    user_svc.set_earnings(user_id, weekly=week_total, monthly=month_total)
    return saved


@router.get("/{char_name}/checklist/{weekly_key}", response_model=BossChecklist)
def get_checklist(
    user_id: str,
    char_name: str,
    weekly_key: str,
    char_svc: CharacterService = Depends(get_character_service),
):
    result = char_svc.get_checklist(user_id, weekly_key, char_name)
    if not result:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return result


@router.get("/{char_name}/cleared-monthly", response_model=dict)
def get_cleared_monthly_bosses(
    user_id: str,
    char_name: str,
    weekly_key: str,
    char_svc: CharacterService = Depends(get_character_service),
):
    """
    현재 주차가 속한 달의 모든 주차에서 클리어된 월간 보스 목록 반환.
    Frontend에서 disabled UI 상태를 정확히 결정하기 위해 사용.
    """
    cleared = char_svc._get_monthly_bosses_cleared_this_month(user_id, weekly_key)
    return {"cleared_monthly_bosses": list(cleared)}


