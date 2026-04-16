"""
13명 멤버 유저 시드 스크립트.

사용법:
  cd backend
  cp .env.example .env  # AWS 자격증명 + API Key 설정 후
  python scripts/seed.py

이미 존재하는 유저는 건너뜁니다 (idempotent).
초기 비밀번호: maple1234 (각 멤버에게 전달 후 변경 권장)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.services.dynamo import DynamoClient
from app.models.user import UserInDB
from app.models.character import Character
from app.utils.password import hash_password
from datetime import datetime

# ── 13명 본캐 닉네임 (user_id = 본캐 닉네임) ────────────────────
INITIAL_PASSWORD = "maple1234"

MEMBERS = [
    {"user_id": "쿄큐렌",     "display_name": "쿄큐렌"},
    {"user_id": "우와블",     "display_name": "우와블"},
    {"user_id": "코앤",       "display_name": "코앤"},
    {"user_id": "고갓",       "display_name": "고갓"},
    {"user_id": "엣뚱",       "display_name": "엣뚱"},
    {"user_id": "귤냠",       "display_name": "귤냠"},
    {"user_id": "지키치키",   "display_name": "지키치키"},
    {"user_id": "딩팬무",     "display_name": "딩팬무"},
    {"user_id": "쿼티윈브",   "display_name": "쿼티윈브"},
    {"user_id": "사뜨",       "display_name": "사뜨"},
    {"user_id": "봉텀",       "display_name": "봉텀"},
    {"user_id": "행뽀칸하루", "display_name": "행뽀칸하루"},
    {"user_id": "잠꾸부엉",   "display_name": "잠꾸부엉"},
]


def seed():
    db = DynamoClient()
    now = datetime.utcnow().isoformat()
    pw_hash = hash_password(INITIAL_PASSWORD)
    created, skipped = 0, 0

    for m in MEMBERS:
        pk = f"USER#{m['user_id']}"
        existing = db.get_item(pk, "METADATA")
        if existing:
            print(f"  [SKIP] {m['user_id']} — 이미 존재")
            skipped += 1
            continue

        # 유저 메타데이터 저장
        record = UserInDB(
            user_id=m["user_id"],
            display_name=m["display_name"],
            password_hash=pw_hash,
            created_at=now,
            updated_at=now,
        )
        db.put_item(record.model_dump())

        # 본캐 캐릭터 자동 등록
        main_char = Character(char_name=m["user_id"], user_id=m["user_id"])
        char_dict = main_char.model_dump()
        char_dict["is_main"] = True
        db.put_item(char_dict)

        print(f"  [OK]   {m['user_id']} 생성 완료 (본캐 자동 등록)")
        created += 1

    print(f"\n완료: {created}명 생성, {skipped}명 건너뜀")
    print(f"초기 비밀번호: {INITIAL_PASSWORD}  ← 각 멤버에게 공유 후 변경 권장")


if __name__ == "__main__":
    settings = get_settings()
    print(f"DynamoDB 테이블: {settings.dynamodb_table_name}")
    print(f"AWS 리전: {settings.aws_region}\n")
    seed()
