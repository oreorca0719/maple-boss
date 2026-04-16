from typing import Optional

from app.models.party import Party, PartyCreate
from app.services.dynamo import DynamoClient


class PartyService:
    def __init__(self, db: DynamoClient) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # 생성
    # ------------------------------------------------------------------

    def create(
        self,
        payload: PartyCreate,
        created_by: str,
        registered_member_ids: list[str],  # 가입된 멤버 user_id (창성자 제외)
    ) -> Party:
        # ── 중복 체크 ─────────────────────────────────────────────────
        existing = self._list_created_by(created_by)
        new_members = sorted((m.user_id, m.char_name) for m in payload.members)
        for p in existing:
            if (
                p.boss_name == payload.boss_name
                and p.difficulty == payload.difficulty
                and sorted((m.user_id, m.char_name) for m in p.members) == new_members
            ):
                raise ValueError("동일한 파티가 이미 존재합니다.")

        # ── 메인 파티 아이템 저장 ──────────────────────────────────────
        party = Party(**payload.model_dump(), created_by=created_by)
        self._db.put_item(party.model_dump())

        # ── 멤버 동기화 아이템 저장 (창성자·외부인 제외, 가입된 멤버만) ─
        for uid in registered_member_ids:
            if uid == created_by:
                continue
            member_item = party.model_dump()
            # 원본 party PK/SK 보존
            member_item["orig_pk"] = member_item["pk"]
            member_item["orig_sk"] = member_item["sk"]
            # 이 아이템의 PK/SK는 유저 파티션
            member_item["pk"] = f"USER#{uid}"
            member_item["sk"] = f"MEMBER_PARTY#{party.party_id}"
            # GSI 필드 제거 (중복 인덱싱 불필요)
            member_item.pop("gsi1pk", None)
            member_item.pop("gsi1sk", None)
            self._db.put_item(member_item)

        return party

    # ------------------------------------------------------------------
    # 조회
    # ------------------------------------------------------------------

    def get(self, scheduled_date: str, sk: str) -> Optional[Party]:
        item = self._db.get_item(pk=f"PARTY#{scheduled_date}", sk=sk)
        return Party(**item) if item else None

    def list_by_date(self, scheduled_date: str) -> list[Party]:
        items = self._db.query_by_pk(
            pk=f"PARTY#{scheduled_date}", sk_begins_with="TIME#"
        )
        return [Party(**item) for item in items]

    def list_by_user(self, user_id: str, date_prefix: Optional[str] = None) -> list[Party]:
        """창성자이거나 멤버로 참여한 모든 파티 반환 (중복 제거)"""
        seen: set[str] = set()
        parties: list[Party] = []

        # 1. 창성자로 만든 파티 (GSI1)
        for p in self._list_created_by(user_id, date_prefix):
            if p.party_id not in seen:
                seen.add(p.party_id)
                parties.append(p)

        # 2. 멤버로 참여한 파티 (USER# PK 직접 조회)
        member_items = self._db.query_by_pk(
            pk=f"USER#{user_id}",
            sk_begins_with="MEMBER_PARTY#",
        )
        for item in member_items:
            try:
                item_copy = dict(item)
                # 원본 PK/SK 복원
                item_copy["pk"] = item_copy.pop("orig_pk", item_copy["pk"])
                item_copy["sk"] = item_copy.pop("orig_sk", item_copy["sk"])
                p = Party(**item_copy)
                if p.party_id not in seen:
                    seen.add(p.party_id)
                    parties.append(p)
            except Exception:
                pass

        return parties

    # ------------------------------------------------------------------
    # 삭제
    # ------------------------------------------------------------------

    def delete(self, scheduled_date: str, sk: str) -> None:
        # 멤버 동기화 아이템도 함께 삭제
        item = self._db.get_item(pk=f"PARTY#{scheduled_date}", sk=sk)
        if item:
            try:
                party = Party(**item)
                party_id = party.party_id
                for member in party.members:
                    uid = member.user_id if hasattr(member, "user_id") else member["user_id"]
                    is_ext = member.is_external if hasattr(member, "is_external") else member.get("is_external", False)
                    if uid != party.created_by and not is_ext:
                        self._db.delete_item(
                            pk=f"USER#{uid}",
                            sk=f"MEMBER_PARTY#{party_id}",
                        )
            except Exception:
                pass

        self._db.delete_item(pk=f"PARTY#{scheduled_date}", sk=sk)

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _list_created_by(
        self, user_id: str, date_prefix: Optional[str] = None
    ) -> list[Party]:
        gsi1sk_prefix = f"PARTY#{date_prefix}" if date_prefix else "PARTY#"
        items = self._db.query_by_gsi1(
            gsi1pk=f"USER#{user_id}",
            gsi1sk_begins_with=gsi1sk_prefix,
        )
        return [Party(**item) for item in items]
