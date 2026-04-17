"""
FastAPI 의존성 주입(DI) 팩토리.
모든 서비스 인스턴스를 여기서 생성하여 라우터에 주입.
"""

from functools import lru_cache
from fastapi import Depends

from app.config import get_settings
from app.services.dynamo import DynamoClient
from app.services.user_service import UserService
from app.services.character_service import CharacterService
from app.services.party_service import PartyService
from app.external.nexon_api import NexonApiClient
from app.ai.service import AIService


@lru_cache
def get_dynamo_client() -> DynamoClient:
    """DynamoClient는 앱 수명 동안 싱글톤으로 유지"""
    return DynamoClient()


@lru_cache
def get_nexon_client() -> NexonApiClient:
    return NexonApiClient()


def get_user_service(db: DynamoClient = Depends(get_dynamo_client)) -> UserService:
    return UserService(db)


def get_character_service(db: DynamoClient = Depends(get_dynamo_client)) -> CharacterService:
    return CharacterService(db)


def get_party_service(db: DynamoClient = Depends(get_dynamo_client)) -> PartyService:
    return PartyService(db)


@lru_cache
def get_ai_service(
    char_service: CharacterService = Depends(get_character_service),
    user_service: UserService = Depends(get_user_service),
) -> AIService:
    """AIService는 앱 수명 동안 싱글톤으로 유지"""
    data_service = None  # 필요시 추가
    return AIService(
        char_service=char_service,
        user_service=user_service,
        data_service=data_service
    )
