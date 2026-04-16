from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class PartyMember(BaseModel):
    user_id: str
    display_name: str
    char_name: str = Field(..., description="파티에 참여하는 캐릭터 명")
    is_external: bool = Field(default=False, description="서비스 미가입 외부인 여부")


class PartyCreate(BaseModel):
    boss_name: str = Field(..., description="보스 이름")
    difficulty: str = Field(..., description="난이도")
    scheduled_date: str = Field(..., description="날짜 (YYYY-MM-DD)")
    scheduled_time: str = Field(..., description="시간 (HH:MM)")
    members: list[PartyMember] = Field(..., min_length=1, max_length=6)
    memo: Optional[str] = Field(default=None, description="파티 메모")


class Party(PartyCreate):
    """API 응답 + DynamoDB 저장 통합 모델"""
    party_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_by: str = Field(..., description="파티 생성자 user_id")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    # DynamoDB Single Table 키
    pk: str = ""   # PARTY#<scheduled_date>
    sk: str = ""   # TIME#<HHMM>#<party_id>

    # GSI: 유저별 참여 파티 조회
    gsi1pk: str = ""   # USER#<created_by>
    gsi1sk: str = ""   # PARTY#<scheduled_date>#<HHMM>

    def model_post_init(self, __context) -> None:
        time_no_colon = self.scheduled_time.replace(":", "")
        if not self.pk:
            self.pk = f"PARTY#{self.scheduled_date}"
        if not self.sk:
            self.sk = f"TIME#{time_no_colon}#{self.party_id}"
        if not self.gsi1pk:
            self.gsi1pk = f"USER#{self.created_by}"
        if not self.gsi1sk:
            self.gsi1sk = f"PARTY#{self.scheduled_date}#{time_no_colon}"
