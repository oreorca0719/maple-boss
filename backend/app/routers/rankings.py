from fastapi import APIRouter, Depends

from app.services.character_service import CharacterService
from app.services.party_service import PartyService
from app.dependencies import get_character_service, get_party_service

router = APIRouter(prefix="/rankings", tags=["rankings"])


@router.get("/party-participation/{weekly_key}")
def get_party_participation_ranking(
    weekly_key: str,
    limit: int = 10,
    char_svc: CharacterService = Depends(get_character_service),
    party_svc: PartyService = Depends(get_party_service),
):
    """주간 파티 참여 순위 - 사용자별 모든 캐릭터 파티 참여 수 합산"""
    return char_svc.get_party_participation_ranking(party_svc, weekly_key, limit)
