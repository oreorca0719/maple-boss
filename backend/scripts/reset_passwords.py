#!/usr/bin/env python3
"""모든 유저의 비밀번호를 1234로 재설정"""

import boto3
from boto3.dynamodb.conditions import Key
import bcrypt
from datetime import datetime
import sys
from app.config import get_settings

def hash_password(password: str) -> str:
    """비밀번호를 bcrypt로 해싱"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def reset_passwords():
    settings = get_settings()
    kwargs = {"region_name": settings.aws_region}
    if settings.dynamodb_endpoint_url:
        kwargs["endpoint_url"] = settings.dynamodb_endpoint_url

    dynamodb = boto3.resource("dynamodb", **kwargs)
    table = dynamodb.Table(settings.dynamodb_table_name)

    print(f"테이블: {settings.dynamodb_table_name}")
    print("=" * 60)

    # 1. 캐릭터에서 모든 user_id 추출 (중복 제거)
    print("\n[1/2] 캐릭터에서 user_id 추출 중...")
    users = table.scan(FilterExpression=Key("pk").begins_with("USER#"))
    char_items = [u for u in users.get("Items", []) if u["sk"].startswith("CHAR#")]

    unique_user_ids = set()
    for char in char_items:
        user_id = char["pk"].replace("USER#", "")
        unique_user_ids.add(user_id)

    print(f"[OK] {len(unique_user_ids)}명의 유저 발견")

    # 2. 각 유저에 대해 METADATA 생성
    print(f"\n[2/2] METADATA 생성 중 (비밀번호: 1234)...")
    password_hash = hash_password("1234")
    now = datetime.utcnow().isoformat()

    created_count = 0
    for user_id in unique_user_ids:
        metadata_item = {
            "pk": f"USER#{user_id}",
            "sk": "METADATA",
            "user_id": user_id,
            "display_name": user_id,  # display_name이 없으면 user_id 사용
            "password_hash": password_hash,
            "weekly_earnings": 0,
            "monthly_earnings": 0,
            "created_at": now,
            "updated_at": now,
        }
        table.put_item(Item=metadata_item)
        created_count += 1

    print(f"[OK] {created_count}개 METADATA 생성")

    print("\n" + "=" * 60)
    print("[OK] 비밀번호 재설정 완료!")
    print(f"\n생성된 유저: {created_count}명")
    print("기본 비밀번호: 1234")

if __name__ == "__main__":
    try:
        reset_passwords()
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
