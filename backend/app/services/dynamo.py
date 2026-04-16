"""
DynamoDB Single Table 기반 범용 CRUD 클라이언트.

테이블 구조:
  PK (String)  |  SK (String)  | GSI1PK (String) | GSI1SK (String) | ...data attrs...
  -------------------------------------------------------------------------------------------------
  USER#<id>    |  METADATA     |                 |                 | display_name, earnings, ...
  USER#<id>    |  CHAR#<name>  |                 |                 | job, level, combat_power, ...
  USER#<id>    |  BOSS_CHECK#<week>#<char> |    |                 | bosses[], total_earnings
  PARTY#<date> |  TIME#<hhmm>#<party_id>  | USER#<creator> | PARTY#<date>#<hhmm> | members[], ...
"""

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from typing import Any, Optional
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)


class DynamoClient:
    def __init__(self) -> None:
        settings = get_settings()
        kwargs: dict[str, Any] = {"region_name": settings.aws_region}

        # 로컬 개발: endpoint_url 주입 (DynamoDB Local)
        if settings.dynamodb_endpoint_url:
            kwargs["endpoint_url"] = settings.dynamodb_endpoint_url

        # ECS Task Role 환경에서는 boto3가 자동으로 IAM Role 자격증명을 사용
        # 로컬 개발 시 AWS CLI 프로파일 또는 환경변수(AWS_ACCESS_KEY_ID 등) 사용
        self._resource = boto3.resource("dynamodb", **kwargs)
        self._table = self._resource.Table(settings.dynamodb_table_name)

    # ------------------------------------------------------------------
    # 기본 CRUD
    # ------------------------------------------------------------------

    def put_item(self, item: dict[str, Any]) -> None:
        """아이템 생성 또는 전체 덮어쓰기"""
        self._table.put_item(Item=item)

    def get_item(self, pk: str, sk: str) -> Optional[dict[str, Any]]:
        """PK + SK로 단건 조회"""
        response = self._table.get_item(Key={"pk": pk, "sk": sk})
        return response.get("Item")

    def update_item(
        self,
        pk: str,
        sk: str,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        """지정한 필드만 업데이트. updates = {"field": value, ...}"""
        if not updates:
            return {}

        expr_parts = []
        expr_names: dict[str, str] = {}
        expr_values: dict[str, Any] = {}

        for i, (key, value) in enumerate(updates.items()):
            placeholder = f"#f{i}"
            value_key = f":v{i}"
            expr_parts.append(f"{placeholder} = {value_key}")
            expr_names[placeholder] = key
            expr_values[value_key] = value

        response = self._table.update_item(
            Key={"pk": pk, "sk": sk},
            UpdateExpression="SET " + ", ".join(expr_parts),
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ReturnValues="ALL_NEW",
        )
        return response.get("Attributes", {})

    def delete_item(self, pk: str, sk: str) -> None:
        """PK + SK로 단건 삭제"""
        self._table.delete_item(Key={"pk": pk, "sk": sk})

    # ------------------------------------------------------------------
    # 쿼리
    # ------------------------------------------------------------------

    def query_by_pk(
        self,
        pk: str,
        sk_begins_with: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """PK로 조회. sk_begins_with가 있으면 SK prefix 필터 추가"""
        key_cond = Key("pk").eq(pk)
        if sk_begins_with:
            key_cond = key_cond & Key("sk").begins_with(sk_begins_with)

        response = self._table.query(
            KeyConditionExpression=key_cond,
            Limit=limit,
        )
        return response.get("Items", [])

    def query_by_gsi1(
        self,
        gsi1pk: str,
        gsi1sk_begins_with: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """GSI1(gsi1pk, gsi1sk)로 조회. 유저별 파티 목록 조회에 사용"""
        key_cond = Key("gsi1pk").eq(gsi1pk)
        if gsi1sk_begins_with:
            key_cond = key_cond & Key("gsi1sk").begins_with(gsi1sk_begins_with)

        response = self._table.query(
            IndexName="GSI1",
            KeyConditionExpression=key_cond,
            Limit=limit,
        )
        return response.get("Items", [])

    # ------------------------------------------------------------------
    # 테이블 초기화 유틸 (로컬 개발용)
    # ------------------------------------------------------------------

    def create_table_if_not_exists(self, table_name: str) -> None:
        """로컬 개발 시 테이블이 없으면 생성"""
        try:
            self._resource.meta.client.describe_table(TableName=table_name)
            logger.info(f"Table '{table_name}' already exists.")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                self._resource.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {"AttributeName": "pk", "KeyType": "HASH"},
                        {"AttributeName": "sk", "KeyType": "RANGE"},
                    ],
                    AttributeDefinitions=[
                        {"AttributeName": "pk", "AttributeType": "S"},
                        {"AttributeName": "sk", "AttributeType": "S"},
                        {"AttributeName": "gsi1pk", "AttributeType": "S"},
                        {"AttributeName": "gsi1sk", "AttributeType": "S"},
                    ],
                    GlobalSecondaryIndexes=[
                        {
                            "IndexName": "GSI1",
                            "KeySchema": [
                                {"AttributeName": "gsi1pk", "KeyType": "HASH"},
                                {"AttributeName": "gsi1sk", "KeyType": "RANGE"},
                            ],
                            "Projection": {"ProjectionType": "ALL"},
                        }
                    ],
                    BillingMode="PAY_PER_REQUEST",
                )
                logger.info(f"Table '{table_name}' created.")
            else:
                raise
