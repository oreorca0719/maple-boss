from fastapi import APIRouter
from app.data.bosses import BOSS_LIST, BossInfo

router = APIRouter(prefix="/bosses", tags=["bosses"])


@router.get("", response_model=list[BossInfo])
def list_bosses():
    """보스 마스터 데이터 목록 (이름, 난이도, 결정석 가격)"""
    return BOSS_LIST
