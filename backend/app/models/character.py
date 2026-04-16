from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class BossEntry(BaseModel):
    boss_name: str = Field(..., description="보스 이름 (예: 카오스 벨룸)")
    difficulty: str = Field(..., description="난이도 (노말/하드/카오스)")
    crystal_price: int = Field(..., description="결정석 가격 (메소)")
    party_size: int = Field(default=1, ge=1, le=6, description="파티 인원 수")
    is_cleared: bool = Field(default=False, description="클리어 여부")
    is_monthly: bool = Field(default=False, description="월간 보스 여부")

    @property
    def earnings(self) -> int:
        """1인당 수익 = 결정석 가격 / 파티 인원"""
        return self.crystal_price // self.party_size


class BossChecklist(BaseModel):
    """캐릭터 주간 보스 체크리스트 (주간 최대 12개 + 월간 보스, 총 13개)"""
    user_id: str
    char_name: str
    weekly_key: str = Field(..., description="주차 키 (YYYY-WW 형식)")
    bosses: list[BossEntry] = Field(default_factory=list, max_length=13)
    total_earnings: int = 0

    # DynamoDB Single Table 키
    pk: str = ""   # USER#<user_id>
    sk: str = ""   # BOSS_CHECK#<weekly_key>#<char_name>

    def model_post_init(self, __context) -> None:
        if not self.pk:
            self.pk = f"USER#{self.user_id}"
        if not self.sk:
            self.sk = f"BOSS_CHECK#{self.weekly_key}#{self.char_name}"

        # 주간 보스 개수 검증 (최대 12개)
        weekly_bosses = [b for b in self.bosses if not b.is_monthly]
        if len(weekly_bosses) > 12:
            raise ValueError("주간 보스는 최대 12개까지만 선택 가능합니다.")

        # 주간 수익만 계산 (월간 보스 제외)
        self.total_earnings = sum(b.earnings for b in self.bosses if b.is_cleared and not b.is_monthly)


class CharacterBase(BaseModel):
    char_name: str = Field(..., description="캐릭터 명 (넥슨 고유 닉네임)")
    user_id: str = Field(..., description="소유 유저 ID")


class CharacterCreate(CharacterBase):
    """캐릭터 등록 요청: char_name만 있으면 API에서 나머지 자동 조회"""
    pass


class CharacterUpdate(BaseModel):
    """넥슨 API에서 갱신한 데이터로 업데이트"""
    job: Optional[str] = None
    job_detail: Optional[str] = None
    level: Optional[int] = None
    combat_power: Optional[int] = None
    image_url: Optional[str] = None
    server: Optional[str] = None


class Character(CharacterBase):
    """API 응답 + DynamoDB 저장 통합 모델"""
    job: str = ""
    job_detail: str = ""
    level: int = 0
    combat_power: int = 0
    image_url: str = ""
    server: str = ""
    synced_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    # DynamoDB Single Table 키
    pk: str = ""   # USER#<user_id>
    sk: str = ""   # CHAR#<char_name>

    def model_post_init(self, __context) -> None:
        if not self.pk:
            self.pk = f"USER#{self.user_id}"
        if not self.sk:
            self.sk = f"CHAR#{self.char_name}"
