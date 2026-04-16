#!/usr/bin/env python3
"""특정 사용자를 관리자로 설정"""

import boto3
import sys
from app.config import get_settings

def set_admin(user_id: str):
    settings = get_settings()
    kwargs = {"region_name": settings.aws_region}
    if settings.dynamodb_endpoint_url:
        kwargs["endpoint_url"] = settings.dynamodb_endpoint_url

    dynamodb = boto3.resource("dynamodb", **kwargs)
    table = dynamodb.Table(settings.dynamodb_table_name)

    print(f"테이블: {settings.dynamodb_table_name}")
    print("=" * 60)
    print(f"\n사용자 '{user_id}'를 관리자로 설정 중...")

    # 기존 사용자 확인
    response = table.get_item(Key={"pk": f"USER#{user_id}", "sk": "METADATA"})
    if "Item" not in response:
        print(f"[ERROR] 사용자 '{user_id}'를 찾을 수 없습니다.")
        return False

    # 관리자 설정
    table.update_item(
        Key={"pk": f"USER#{user_id}", "sk": "METADATA"},
        UpdateExpression="SET is_admin = :val",
        ExpressionAttributeValues={":val": True}
    )

    print(f"[OK] '{user_id}'를 관리자로 설정했습니다.")
    print("=" * 60)
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python set_admin.py <user_id>")
        print("예: python set_admin.py 쿄큐렌")
        sys.exit(1)

    user_id = sys.argv[1]
    try:
        if set_admin(user_id):
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
