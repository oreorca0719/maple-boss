from datetime import datetime
from typing import Optional

from app.models.user import User, UserCreate, UserUpdate, UserInDB
from app.services.dynamo import DynamoClient


class UserService:
    def __init__(self, db: DynamoClient) -> None:
        self._db = db

    def create(self, payload: UserCreate) -> User:
        """
        유저 생성 + 본캐를 CHAR# 레코드로 자동 등록.
        user_id = 본캐 닉네임이므로 동일 이름으로 캐릭터도 생성.
        """
        from app.models.character import Character

        now = datetime.utcnow().isoformat()
        record = UserInDB(
            user_id=payload.user_id,
            display_name=payload.display_name,
            password_hash=payload.password_hash,
            created_at=now,
            updated_at=now,
        )
        self._db.put_item(record.model_dump())

        # 본캐 캐릭터 자동 등록 (is_main=True 플래그)
        main_char = Character(char_name=payload.user_id, user_id=payload.user_id)
        char_dict = main_char.model_dump()
        char_dict["is_main"] = True
        self._db.put_item(char_dict)

        return User(**record.model_dump())

    def get(self, user_id: str) -> Optional[User]:
        item = self._db.get_item(pk=f"USER#{user_id}", sk="METADATA")
        if not item:
            return None
        return User(**item)

    def get_full(self, user_id: str) -> Optional[UserInDB]:
        """password_hash 포함 전체 레코드 (인증용)"""
        item = self._db.get_item(pk=f"USER#{user_id}", sk="METADATA")
        if not item:
            return None
        return UserInDB(**item)

    def update(self, user_id: str, payload: UserUpdate) -> Optional[User]:
        updates = payload.model_dump(exclude_none=True)
        if not updates:
            return self.get(user_id)
        updates["updated_at"] = datetime.utcnow().isoformat()
        updated = self._db.update_item(
            pk=f"USER#{user_id}", sk="METADATA", updates=updates
        )
        return User(**updated) if updated else None

    def set_earnings(self, user_id: str, weekly: int, monthly: int) -> None:
        """주간/월간 수익을 지정값으로 SET (가산 아님)"""
        self._db.update_item(
            pk=f"USER#{user_id}",
            sk="METADATA",
            updates={
                "weekly_earnings": weekly,
                "monthly_earnings": monthly,
                "updated_at": datetime.utcnow().isoformat(),
            },
        )

    def list_all(self) -> list[User]:
        """고정 멤버 12명 전체 조회 (scan 대신 미리 등록된 user_id 목록 사용 권장)"""
        # 운영환경에서는 별도의 멤버 목록 관리 권장
        # 현재는 scan으로 METADATA 레코드만 조회
        from boto3.dynamodb.conditions import Attr
        response = self._db._table.scan(
            FilterExpression=Attr("sk").eq("METADATA")
        )
        return [User(**item) for item in response.get("Items", [])]

    def list_pending(self) -> list[User]:
        """가입 승인 대기 중인 사용자 조회"""
        from boto3.dynamodb.conditions import Attr
        response = self._db._table.scan(
            FilterExpression=Attr("sk").eq("METADATA") & Attr("is_approved").eq(False)
        )
        return [User(**item) for item in response.get("Items", [])]

    def delete(self, user_id: str) -> None:
        """사용자 및 관련 데이터 삭제"""
        # 사용자 메타데이터 삭제
        self._db.delete_item(pk=f"USER#{user_id}", sk="METADATA")

        # 사용자의 모든 캐릭터, 체크리스트, 파티 등 삭제
        from boto3.dynamodb.conditions import Key
        items = self._db._table.query(
            KeyConditionExpression=Key("pk").eq(f"USER#{user_id}")
        )
        for item in items.get("Items", []):
            self._db.delete_item(pk=item["pk"], sk=item["sk"])
