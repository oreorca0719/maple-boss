#!/usr/bin/env python3
"""
DynamoDB 초기화 스크립트
- 유저 누적 수익 (USER#<id> / METADATA)
- 주간 보스 체크리스트 (USER#<id> / BOSS_CHECK#...)
- 파티 일정 (PARTY#<date> / TIME#...)
- 멤버 파티 동기화 (USER#<id> / MEMBER_PARTY#...)

캐릭터 정보(CHAR#)는 유지합니다.
"""

import boto3
from boto3.dynamodb.conditions import Key
import sys
from app.config import get_settings

def reset_db():
    settings = get_settings()
    kwargs = {"region_name": settings.aws_region}
    if settings.dynamodb_endpoint_url:
        kwargs["endpoint_url"] = settings.dynamodb_endpoint_url

    dynamodb = boto3.resource("dynamodb", **kwargs)
    table = dynamodb.Table(settings.dynamodb_table_name)

    print(f"테이블: {settings.dynamodb_table_name}")
    print("=" * 60)

    # 1. 모든 PARTY 항목 삭제
    print("\n[1/4] 파티 일정 삭제 중...")
    parties = table.scan(FilterExpression=Key("pk").begins_with("PARTY#"))
    party_count = 0
    for item in parties.get("Items", []):
        table.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})
        party_count += 1
    print(f"[OK] {party_count}개 파티 삭제")

    # 2. 모든 USER items에서 METADATA, BOSS_CHECK, MEMBER_PARTY 삭제
    print("\n[2/4] 유저 데이터 삭제 중...")
    users = table.scan(FilterExpression=Key("pk").begins_with("USER#"))

    metadata_count = 0
    boss_check_count = 0
    member_party_count = 0

    for item in users.get("Items", []):
        pk = item["pk"]
        sk = item["sk"]

        # METADATA 삭제
        if sk == "METADATA":
            table.delete_item(Key={"pk": pk, "sk": sk})
            metadata_count += 1

        # BOSS_CHECK 삭제
        elif sk.startswith("BOSS_CHECK#"):
            table.delete_item(Key={"pk": pk, "sk": sk})
            boss_check_count += 1

        # MEMBER_PARTY 삭제
        elif sk.startswith("MEMBER_PARTY#"):
            table.delete_item(Key={"pk": pk, "sk": sk})
            member_party_count += 1

    print(f"[OK] METADATA {metadata_count}개 삭제")
    print(f"[OK] 보스 체크리스트 {boss_check_count}개 삭제")
    print(f"[OK] 멤버 파티 {member_party_count}개 삭제")

    # 3. EARNINGS 항목도 삭제 (부가 정보)
    print("\n[3/4] 수익 기록 삭제 중...")
    earnings_items = table.scan(FilterExpression=Key("sk").begins_with("EARNINGS#"))
    earnings_count = 0
    for item in earnings_items.get("Items", []):
        table.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})
        earnings_count += 1
    print(f"[OK] {earnings_count}개 수익 기록 삭제")

    print("\n[4/4] 최종 확인...")
    print("=" * 60)
    print("[OK] 초기화 완료!")
    print("\n유지된 데이터:")
    print("  - 캐릭터 정보 (USER#<id> / CHAR#<name>)")
    print("\n삭제된 데이터:")
    print(f"  - 유저 누적 수익 ({metadata_count}개)")
    print(f"  - 주간 보스 체크리스트 ({boss_check_count}개)")
    print(f"  - 파티 일정 ({party_count}개)")
    print(f"  - 멤버 파티 동기화 ({member_party_count}개)")
    print(f"  - 수익 기록 ({earnings_count}개)")

if __name__ == "__main__":
    try:
        reset_db()
    except Exception as e:
        print(f"[ERROR] 오류: {e}")
        sys.exit(1)
