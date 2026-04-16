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

    def save_checklist(self, checklist: BossChecklist) -> tuple[BossChecklist, int, int]:
        """
        체크리스트 저장.
        저장 후 이번 주 전체 캐릭터 합산으로 weekly/monthly를 재계산(SET).
        가산(+=) 방식을 쓰지 않으므로 몇 번 저장해도 수치가 불어나지 않음.
        반환: (저장된 체크리스트, 이번주 합계, 이번달 합계)
        """
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
