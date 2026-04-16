#!/usr/bin/env python3
"""모든 유저의 비밀번호를 1234로 재설정 + 현재 주차 수익 복구"""

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

def get_current_week_key() -> str:
    """현재 주차 키 (YYYY-Www) 계산"""
    now = datetime.utcnow()
    jan4 = datetime(now.year, 1, 4)
    from datetime import timedelta
    weekOne = jan4.replace(hour=0, minute=0, second=0, microsecond=0)
    weekOne = weekOne - timedelta(days=jan4.weekday())
    daysDiff = (now - weekOne).days
    week = (daysDiff // 7) + 1
    return f"{now.year}-W{str(week).zfill(2)}"

def reset_passwords_v2():
    settings = get_settings()
    kwargs = {"region_name": settings.aws_region}
    if settings.dynamodb_endpoint_url:
        kwargs["endpoint_url"] = settings.dynamodb_endpoint_url

    dynamodb = boto3.resource("dynamodb", **kwargs)
    table = dynamodb.Table(settings.dynamodb_table_name)

    print(f"테이블: {settings.dynamodb_table_name}")
    print("=" * 60)

    # 1. 캐릭터에서 모든 user_id 추출
    print("\n[1/3] 캐릭터에서 user_id 추출 중...")
    users = table.scan(FilterExpression=Key("pk").begins_with("USER#"))
    char_items = [u for u in users.get("Items", []) if u["sk"].startswith("CHAR#")]

    unique_user_ids = set()
    for char in char_items:
        user_id = char["pk"].replace("USER#", "")
        unique_user_ids.add(user_id)

    print(f"[OK] {len(unique_user_ids)}명의 유저 발견")

    # 2. 현재 주차 수익 조회
    print("\n[2/3] 현재 주차 수익 조회 중...")
    current_week = get_current_week_key()
    print(f"현재 주차: {current_week}")

    user_earnings = {}
    for user_id in unique_user_ids:
        try:
            earnings_item = table.get_item(Key={
                "pk": f"USER#{user_id}",
                "sk": f"EARNINGS#{current_week}"
            })
            if "Item" in earnings_item:
                weekly = earnings_item["Item"].get("total_earnings", 0)
                user_earnings[user_id] = weekly
                print(f"  {user_id}: {weekly}")
            else:
                user_earnings[user_id] = 0
        except Exception as e:
            print(f"  {user_id}: 오류 ({e})")
            user_earnings[user_id] = 0

    # 3. METADATA 생성 (수익 정보 포함)
    print(f"\n[3/3] METADATA 생성 중 (비밀번호: 1234)...")
    password_hash = hash_password("1234")
    now = datetime.utcnow().isoformat()

    created_count = 0
    for user_id in unique_user_ids:
        weekly_earnings = user_earnings.get(user_id, 0)
        metadata_item = {
            "pk": f"USER#{user_id}",
            "sk": "METADATA",
            "user_id": user_id,
            "display_name": user_id,
            "password_hash": password_hash,
            "weekly_earnings": weekly_earnings,
            "monthly_earnings": 0,  # 월간 수익은 별도 로직으로 계산 필요
            "created_at": now,
            "updated_at": now,
        }
        table.put_item(Item=metadata_item)
        created_count += 1

    print(f"[OK] {created_count}개 METADATA 생성")

    print("\n" + "=" * 60)
    print("[OK] 비밀번호 재설정 완료!")
    print(f"\n생성된 유저: {created_count}명")
    print(f"수익 복구: {current_week} 주간 수익 적용")
    print("기본 비밀번호: 1234")

if __name__ == "__main__":
    try:
        reset_passwords_v2()
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
