#!/usr/bin/env python3
"""DynamoDB 현재 상태 확인"""

import boto3
from boto3.dynamodb.conditions import Key
import sys
from app.config import get_settings

def check_db():
    settings = get_settings()
    kwargs = {"region_name": settings.aws_region}
    if settings.dynamodb_endpoint_url:
        kwargs["endpoint_url"] = settings.dynamodb_endpoint_url

    dynamodb = boto3.resource("dynamodb", **kwargs)
    table = dynamodb.Table(settings.dynamodb_table_name)

    print(f"테이블: {settings.dynamodb_table_name}")
    print("=" * 60)

    # 1. USER 항목 확인
    print("\n[USER 항목]")
    users = table.scan(FilterExpression=Key("pk").begins_with("USER#"))
    user_items = users.get("Items", [])

    metadata_users = [u for u in user_items if u["sk"] == "METADATA"]
    char_users = [u for u in user_items if u["sk"].startswith("CHAR#")]

    print(f"METADATA (유저 인증 정보): {len(metadata_users)}개")
    for user in metadata_users:
        print(f"  - {user['pk']}")

    print(f"CHAR (캐릭터 정보): {len(char_users)}개")
    for char in char_users:
        print(f"  - {char['pk']} / {char['sk']}")

    # 2. PARTY 항목 확인
    print("\n[PARTY 항목]")
    parties = table.scan(FilterExpression=Key("pk").begins_with("PARTY#"))
    party_items = parties.get("Items", [])
    print(f"파티 일정: {len(party_items)}개")

    # 3. 기타 항목
    print("\n[기타 항목]")
    boss_checks = [u for u in user_items if u["sk"].startswith("BOSS_CHECK#")]
    earnings = [u for u in user_items if u["sk"].startswith("EARNINGS#")]
    member_parties = [u for u in user_items if u["sk"].startswith("MEMBER_PARTY#")]

    print(f"보스 체크리스트: {len(boss_checks)}개")
    print(f"수익 기록: {len(earnings)}개")
    print(f"멤버 파티: {len(member_parties)}개")

if __name__ == "__main__":
    try:
        check_db()
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
