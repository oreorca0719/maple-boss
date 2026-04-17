"""
AI Service FastAPI 통합 테스트
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from app.main import create_app
from app.ai.service import AIService


@pytest.fixture
def client():
    """FastAPI 테스트 클라이언트"""
    app = create_app()
    return TestClient(app)


class TestAIRouterIntegration:
    """AI Router FastAPI 통합 테스트"""

    def test_health_check(self, client):
        """헬스 체크 엔드포인트 테스트"""
        response = client.get("/health")
        assert response.status_code == 200, "헬스 체크 실패"
        assert response.json()["status"] == "ok", "상태가 ok가 아님"

    def test_chat_endpoint_exists(self, client):
        """채팅 엔드포인트 존재 확인"""
        # 엔드포인트 존재 여부 확인 (실제 실행은 아님)
        response = client.post(
            "/api/v1/ai/chat",
            json={
                "user_id": "test_user",
                "message": "테스트"
            }
        )
        # 500 에러 또는 422 (validation)이 올 수 있음
        # 중요한 건 엔드포인트가 존재한다는 것
        assert response.status_code in [200, 422, 500], f"예상 밖의 상태 코드: {response.status_code}"

    def test_chat_empty_message(self, client):
        """빈 메시지 검증"""
        response = client.post(
            "/api/v1/ai/chat",
            json={
                "user_id": "test_user",
                "message": ""
            }
        )
        # 빈 메시지는 400 Bad Request를 반환해야 함
        assert response.status_code in [400, 422], f"빈 메시지가 거부되지 않음: {response.status_code}"

    def test_chat_missing_user_id(self, client):
        """user_id 누락 검증"""
        response = client.post(
            "/api/v1/ai/chat",
            json={
                "message": "테스트"
            }
        )
        # user_id 필수 필드 누락 시 422 Unprocessable Entity
        assert response.status_code == 422, "user_id 누락이 검증되지 않음"

    def test_chat_request_structure(self, client):
        """채팅 요청 구조 검증"""
        # 정상 요청 구조 확인
        payload = {
            "user_id": "test_user",
            "message": "보스 수익 분석해줘",
            "char_name": "TestChar"
        }
        
        # 요청은 실패할 수 있지만 구조는 유효해야 함
        response = client.post("/api/v1/ai/chat", json=payload)
        
        # 상태 코드는 다양할 수 있지만 400/422는 아니어야 함 (구조적 오류)
        # 500이나 200이 정상임
        assert response.status_code != 422, "요청 구조가 유효하지 않음"


class TestChatResponseModel:
    """ChatResponse 모델 테스트"""

    def test_chat_response_model_creation(self):
        """ChatResponse 모델 생성 테스트"""
        from app.routers.ai import ChatResponse
        
        response = ChatResponse(
            response="테스트 응답입니다",
            tools_used=["analyze_character_earnings"]
        )
        
        assert response.response == "테스트 응답입니다", "응답 텍스트가 일치하지 않음"
        assert len(response.tools_used) == 1, "도구 목록 길이가 맞지 않음"
        assert response.tools_used[0] == "analyze_character_earnings", "도구 이름이 일치하지 않음"

    def test_chat_request_model_creation(self):
        """ChatRequest 모델 생성 테스트"""
        from app.routers.ai import ChatRequest
        
        request = ChatRequest(
            user_id="test_user",
            message="메시지",
            char_name="TestChar"
        )
        
        assert request.user_id == "test_user", "user_id가 일치하지 않음"
        assert request.message == "메시지", "message가 일치하지 않음"
        assert request.char_name == "TestChar", "char_name이 일치하지 않음"

    def test_chat_request_optional_char_name(self):
        """ChatRequest char_name 선택적 필드 테스트"""
        from app.routers.ai import ChatRequest
        
        request = ChatRequest(
            user_id="test_user",
            message="메시지"
            # char_name 제외
        )
        
        assert request.user_id == "test_user", "user_id가 일치하지 않음"
        assert request.char_name is None, "char_name이 None이 아님"


class TestAIServiceInitialization:
    """AIService 초기화 테스트"""

    def test_ai_service_singleton(self):
        """AIService 싱글톤 확인"""
        from app.dependencies import get_ai_service
        
        # 캐시된 함수 확인
        service1 = get_ai_service()
        service2 = get_ai_service()
        
        assert service1 is service2, "싱글톤이 작동하지 않음"
        assert isinstance(service1, AIService), "AIService 인스턴스가 아님"

    def test_ai_service_has_tools(self):
        """AIService에 도구가 있는지 확인"""
        from app.dependencies import get_ai_service
        
        service = get_ai_service()
        
        assert service.tools is not None, "tools가 None임"
        assert len(service.tools) == 5, f"도구 개수가 5개가 아님: {len(service.tools)}"
        
        tool_names = [tool.name for tool in service.tools]
        expected_tools = [
            "replicate_checklist_from_last_week",
            "analyze_character_earnings",
            "get_character_checklist",
            "analyze_user_earnings",
            "get_top_earning_bosses"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"도구 '{expected_tool}'이 없음"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
