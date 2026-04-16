from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    user_id: str = Field(..., description="유저 고유 ID (로그인 ID)")
    display_name: str = Field(..., description="닉네임 / 표시 이름")


class UserCreate(UserBase):
    password_hash: str = Field(..., description="해시된 패스워드")


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    weekly_earnings: Optional[int] = None  # 주간 누적 수익 (메소)
    monthly_earnings: Optional[int] = None  # 월간 누적 수익 (메소)


class UserInDB(UserBase):
    """DynamoDB에서 읽어온 전체 유저 레코드"""
    password_hash: str
    weekly_earnings: int = 0
    monthly_earnings: int = 0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    # DynamoDB Single Table 키
    pk: str = ""  # USER#<user_id>
    sk: str = "METADATA"

    def model_post_init(self, __context) -> None:
        if not self.pk:
            self.pk = f"USER#{self.user_id}"


class User(UserBase):
    """API 응답용 모델 (password_hash 제외)"""
    weekly_earnings: int = 0
    monthly_earnings: int = 0
    created_at: str
    updated_at: str
