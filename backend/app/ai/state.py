"""
LangGraph AI Agent 상태 정의
"""
from typing import Annotated, Any
from pydantic import BaseModel, Field, field_serializer, field_validator
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from datetime import datetime


class AIState(BaseModel):
    """AI Agent의 상태"""

    user_id: str = Field(..., description="사용자 ID")
    char_name: str | None = Field(None, description="캐릭터 이름")
    messages: Annotated[list, add_messages] = Field(
        default_factory=list,
        description="대화 히스토리"
    )
    current_week: str = Field(..., description="현재 주차 (YYYY-Www)")
    tool_results: dict[str, Any] = Field(
        default_factory=dict,
        description="Tool 실행 결과"
    )
    user_context: dict[str, Any] = Field(
        default_factory=dict,
        description="사용자 추가 정보"
    )
    final_response: str | None = Field(None, description="최종 응답")

    model_config = {
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }

    @field_validator('messages', mode='before')
    @classmethod
    def validate_messages(cls, v):
        """Validate messages, accepting both dict and BaseMessage objects"""
        if not isinstance(v, list):
            return [v] if v else []
        return v

    @field_serializer('messages')
    def serialize_messages(self, messages: list) -> list:
        """Serialize messages, handling both dict and BaseMessage objects"""
        result = []
        for msg in messages:
            if isinstance(msg, dict):
                result.append(msg)
            elif isinstance(msg, BaseMessage):
                result.append({
                    "role": msg.type if hasattr(msg, 'type') else "assistant",
                    "content": msg.content
                })
            else:
                result.append(msg)
        return result
