from datetime import datetime, date as date_type
from typing import Optional, TYPE_CHECKING

from app.models.character import Character, CharacterCreate, CharacterUpdate, BossChecklist
from app.services.dynamo import DynamoClient

if TYPE_CHECKING:
    from app.services.party_service import PartyService


class CharacterService:
    def __init__(self, db: DynamoClient, party_service: Optional["PartyService"] = None) -> None:
        self._db = db
        self._party_service = party_service

    def create(self, payload: CharacterCreate) -> Character:
        char = Character(char_name=payload.char_name, user_id=payload.user_id)
        self._db.put_item(char.model_dump())
        return char

    def get(self, user_id: str, char_name: str) -> Optional[Character]:
        item = self._db.get_item(
            pk=f"USER#{user_id}", sk=f"CHAR#{char_name}"
        )
        return Character(**item) if item else None

    def list_by_user(self, user_id: str) -> list[Character]:
        items = self._db.query_by_pk(pk=f"USER#{user_id}", sk_begins_with="CHAR#")
        return [Character(**item) for item in items]

    def sync_from_api(self, user_id: str, char_name: str, data: CharacterUpdate) -> Optional[Character]:
        """넥슨 API 조회 결과로 캐릭터 정보 갱신"""
        updates = data.model_dump(exclude_none=True)
        updates["synced_at"] = datetime.utcnow().isoformat()
        updated = self._db.update_item(
            pk=f"USER#{user_id}", sk=f"CHAR#{char_name}", updates=updates
        )
        return Character(**updated) if updated else None

    def delete(self, user_id: str, char_name: str) -> None:
        # 캐릭터가 속한 파티들 삭제
        if self._party_service:
            try:
                all_parties = self._party_service.list_by_user(user_id)
                for party in all_parties:
                    # 이 캐릭터가 파티에 속해 있는지 확인
                    if any(m.char_name == char_name for m in party.members):
                        if party.pk and party.sk:
                            scheduled_date = party.pk.replace("PARTY#", "")
                            self._party_service.delete(scheduled_date, party.sk)
            except Exception:
                pass

        # 캐릭터 삭제
        self._db.delete_item(pk=f"USER#{user_id}", sk=f"CHAR#{char_name}")

    # ------------------------------------------------------------------
    # 보스 체크리스트
    # ------------------------------------------------------------------

    def _is_cross_month_week(self, weekly_key: str) -> bool:
        """주가 달을 걸치는지 확인 (목요일과 수요일이 다른 달)"""
        thu = self._weekly_key_to_thursday(weekly_key)
        wed = date_type.fromordinal(thu.toordinal() + 6)  # Thursday + 6 days = Wednesday
        return (thu.year, thu.month) != (wed.year, wed.month)

    def _get_monthly_bosses_cleared_this_month(self, user_id: str, weekly_key: str) -> set[str]:
        """같은 달의 다른 주에서 이미 클리어된 월간 보스 반환 (달 경계 주 제외)"""
        # 현재 주의 월 정보 계산
        thu = self._weekly_key_to_thursday(weekly_key)
        current_ym = (thu.year, thu.month)

        # 달 경계 주이면 중복 방지 미적용 (새로운 달에 다시 선택 가능하도록)
        if self._is_cross_month_week(weekly_key):
            return set()

        # 같은 달의 모든 체크리스트 조회
        items = self._db.query_by_pk(
            pk=f"USER#{user_id}",
            sk_begins_with="BOSS_CHECK#",
            limit=52,
        )

        cleared_monthly = set()
        for item in items:
            try:
                wk = item.get("weekly_key", "")
                wk_thu = self._weekly_key_to_thursday(wk)
                # 같은 달인지 확인 (달 경계 주가 아닌 경우만 카운트)
                if (wk_thu.year, wk_thu.month) == current_ym and not self._is_cross_month_week(wk):
                    bosses = item.get("bosses", [])
                    for boss in bosses:
                        # 월간 보스이고 클리어된 것만 수집
                        if boss.get("is_monthly") and boss.get("is_cleared"):
                            cleared_monthly.add(boss.get("boss_name", ""))
            except Exception:
                pass

        return cleared_monthly

    def save_checklist(self, checklist: BossChecklist) -> tuple[BossChecklist, int, int]:
        """
        체크리스트 저장.
        월간 보스는 같은 달에 1회만 적립 (이미 클리어된 월간 보스는 is_cleared=False로 변경).
        월간 보스가 적립된 주의 주간 수익에 포함됨.
        저장 후 이번 주 전체 캐릭터 합산으로 weekly/monthly를 재계산(SET).
        반환: (저장된 체크리스트, 이번주 합계, 이번달 합계)
        """
        # 0. 월간 보스 중복 제거 (같은 달에 이미 클리어된 월간 보스는 is_cleared=False로 변경)
        cleared_monthly = self._get_monthly_bosses_cleared_this_month(checklist.user_id, checklist.weekly_key)
        for boss in checklist.bosses:
            if boss.is_monthly and boss.boss_name in cleared_monthly:
                boss.is_cleared = False

        # 0-1. total_earnings 재계산 (is_cleared=False로 변경된 월간 보스 제외)
        checklist.total_earnings = sum(b.earnings for b in checklist.bosses if b.is_cleared)

        # 1. 체크리스트 저장 (덮어쓰기)
        self._db.put_item(checklist.model_dump())

        # 2. 이번 주 전체 캐릭터 합산 (저장 직후 쿼리 → 이 캐릭터 포함)
        all_cls = self.list_checklists_by_week(checklist.user_id, checklist.weekly_key)
        week_total = sum(int(c.total_earnings) for c in all_cls)

        # 3. EARNINGS# 레코드 SET (가산 아님)
        self._set_earnings_record(checklist.user_id, checklist.weekly_key, week_total)

        # 4. 이번 달 합산
        month_total = self._compute_month_total(checklist.user_id, checklist.weekly_key)

        return checklist, week_total, month_total

    def _set_earnings_record(self, user_id: str, weekly_key: str, total: int) -> None:
        """EARNINGS# 레코드를 total로 덮어씀"""
        self._db.put_item({
            "pk": f"USER#{user_id}",
            "sk": f"EARNINGS#{weekly_key}",
            "weekly_key": weekly_key,
            "total_earnings": total,
            "updated_at": datetime.utcnow().isoformat(),
        })

    def _weekly_key_to_thursday(self, weekly_key: str) -> date_type:
        """YYYY-Www → 메이플 주 시작일(목요일)"""
        year = int(weekly_key.split("-W")[0])
        week = int(weekly_key.split("-W")[1])
        jan4 = date_type(year, 1, 4)
        monday = date_type.fromordinal(
            jan4.toordinal() - (jan4.isoweekday() - 1) + (week - 1) * 7
        )
        return date_type.fromordinal(monday.toordinal() + 3)

    def _compute_month_total(self, user_id: str, current_weekly_key: str) -> int:
        """current_weekly_key가 속한 달의 모든 주차 EARNINGS# 합산"""
        thu = self._weekly_key_to_thursday(current_weekly_key)
        current_ym = (thu.year, thu.month)

        items = self._db.query_by_pk(
            pk=f"USER#{user_id}",
            sk_begins_with="EARNINGS#",
            limit=52,
        )
        total = 0
        for item in items:
            wk = item.get("weekly_key", "")
            try:
                wk_thu = self._weekly_key_to_thursday(wk)
                if (wk_thu.year, wk_thu.month) == current_ym:
                    total += int(item.get("total_earnings", 0))
            except Exception:
                pass
        return total

    def get_weekly_earnings_history(self, user_id: str, weeks: int = 8) -> list[dict]:
        """최근 N주치 수익 히스토리 반환 (차트용)"""
        items = self._db.query_by_pk(
            pk=f"USER#{user_id}",
            sk_begins_with="EARNINGS#",
            limit=weeks,
        )
        return sorted(items, key=lambda x: x["weekly_key"])

    def get_checklist(self, user_id: str, weekly_key: str, char_name: str) -> Optional[BossChecklist]:
        sk = f"BOSS_CHECK#{weekly_key}#{char_name}"
        item = self._db.get_item(pk=f"USER#{user_id}", sk=sk)
        return BossChecklist(**item) if item else None

    def list_checklists_by_week(self, user_id: str, weekly_key: str) -> list[BossChecklist]:
        """해당 주차의 모든 캐릭터 체크리스트 조회"""
        items = self._db.query_by_pk(
            pk=f"USER#{user_id}",
            sk_begins_with=f"BOSS_CHECK#{weekly_key}#",
        )
        return [BossChecklist(**item) for item in items]

    def get_party_participation_ranking(self, party_service: "PartyService", weekly_key: str, limit: int = 10) -> list[dict]:
        """주간 파티 참여 순위 (user별 모든 캐릭터의 파티 참여 수 합산)"""
        parties = party_service.list_by_week(weekly_key)
        
        user_party_count: dict[str, int] = {}
        for party in parties:
            for member in party.members:
                user_id = member.user_id
                user_party_count[user_id] = user_party_count.get(user_id, 0) + 1
        
        ranking = sorted(
            [{"user_id": uid, "party_count": count} for uid, count in user_party_count.items()],
            key=lambda x: x["party_count"],
            reverse=True
        )[:limit]
        
        return ranking
