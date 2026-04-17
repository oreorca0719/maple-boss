"""
AI Service 통합 테스트
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from app.ai.service import AIService
from app.ai.state import AIState


class TestAIService:
    """AIService 통합 테스트"""

    @pytest.fixture
    def mock_services(self):
        """Mock 서비스 생성"""
        char_service = Mock()
        user_service = Mock()
        data_service = None

        return char_service, user_service, data_service

    @pytest.fixture
    def ai_service(self, mock_services):
        """AIService 인스턴스 생성"""
        char_service, user_service, data_service = mock_services
        return AIService(
            char_service=char_service,
            user_service=user_service,
            data_service=data_service
        )

    def test_ai_service_initialization(self, ai_service):
        """AIService 초기화 테스트"""
        assert ai_service is not None, "AIService가 None임"
        assert ai_service.char_service is not None, "CharacterService가 None임"
        assert ai_service.user_service is not None, "UserService가 None임"
        assert ai_service.graph is not None, "그래프가 None임"
        assert len(ai_service.tools) == 5, "도구 개수가 5개가 아님"

    def test_get_current_week_key(self, ai_service):
        """현재 주차 계산 테스트"""
        week_key = ai_service.get_current_week_key()
        
        # YYYY-Www 형식 확인
        assert week_key.startswith("202"), "연도 형식이 맞지 않음"
        assert "-W" in week_key, "주차 구분자가 없음"
        
        parts = week_key.split("-W")
        assert len(parts) == 2, "주차 형식이 맞지 않음"
        assert len(parts[1]) == 2, "주 번호 형식이 맞지 않음"

    @pytest.mark.asyncio
    async def test_chat_basic_message(self, ai_service, mock_services):
        """기본 메시지 채팅 테스트"""
        # Mock 그래프 설정
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(return_value={
            "final_response": "테스트 응답입니다."
        })
        ai_service.graph = mock_graph

        response = await ai_service.chat(
            user_id="test_user",
            message="안녕하세요",
            char_name="TestChar"
        )

        assert response == "테스트 응답입니다.", "응답이 일치하지 않음"
        assert mock_graph.ainvoke.called, "그래프가 호출되지 않음"

    @pytest.mark.asyncio
    async def test_chat_without_char_name(self, ai_service, mock_services):
        """캐릭터 이름 없이 채팅 테스트"""
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(return_value={
            "final_response": "응답"
        })
        ai_service.graph = mock_graph

        response = await ai_service.chat(
            user_id="test_user",
            message="보스 수익 분석해줘"
        )

        assert response == "응답", "응답이 없음"
        # ainvoke 호출 확인
        call_args = mock_graph.ainvoke.call_args
        state = call_args[0][0]
        assert state.char_name is None, "캐릭터 이름이 설정됨"

    @pytest.mark.asyncio
    async def test_chat_with_error(self, ai_service, mock_services):
        """에러 처리 테스트"""
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(
            side_effect=Exception("Test error")
        )
        ai_service.graph = mock_graph

        response = await ai_service.chat(
            user_id="test_user",
            message="테스트",
            char_name="TestChar"
        )

        assert "오류" in response, "오류 메시지가 없음"
        assert "Test error" in response, "오류 상세가 없음"

    @pytest.mark.asyncio
    async def test_chat_streaming(self, ai_service, mock_services):
        """스트리밍 응답 테스트"""
        # Mock 이벤트 생성
        mock_events = [
            {"llm": {"thread_id": "1"}},
            {"tools": {"thread_id": "1"}},
            {"output": {"final_response": "최종 응답"}},
        ]

        async def mock_astream(state):
            for event in mock_events:
                yield event

        mock_graph = AsyncMock()
        mock_graph.astream = mock_astream
        ai_service.graph = mock_graph

        events = []
        async for event in ai_service.chat_streaming(
            user_id="test_user",
            message="테스트",
            char_name="TestChar"
        ):
            events.append(event)

        assert len(events) == 3, "이벤트 개수가 맞지 않음"
        assert events[-1].get("output") is not None, "마지막 이벤트가 output이 아님"

    @pytest.mark.asyncio
    async def test_chat_streaming_error(self, ai_service, mock_services):
        """스트리밍 에러 처리 테스트"""
        async def mock_astream_error(state):
            raise Exception("Stream error")
            yield None

        mock_graph = AsyncMock()
        mock_graph.astream = mock_astream_error
        ai_service.graph = mock_graph

        error_found = False
        async for event in ai_service.chat_streaming(
            user_id="test_user",
            message="테스트"
        ):
            if event.get("error"):
                error_found = True
                assert "Stream error" in event.get("message", ""), "에러 메시지가 없음"

        assert error_found, "에러가 발생하지 않음"


class TestAIState:
    """AIState 모델 테스트"""

    def test_ai_state_initialization(self):
        """AIState 초기화 테스트"""
        state = AIState(
            user_id="test_user",
            char_name="TestChar",
            messages=[{"role": "user", "content": "테스트"}],
            current_week="2026-W17"
        )

        assert state.user_id == "test_user", "user_id가 일치하지 않음"
        assert state.char_name == "TestChar", "char_name이 일치하지 않음"
        assert len(state.messages) == 1, "메시지 개수가 맞지 않음"
        assert state.current_week == "2026-W17", "current_week이 일치하지 않음"
        assert state.tool_results is None or state.tool_results == {}, "tool_results가 초기화되지 않음"

    def test_ai_state_add_messages(self):
        """메시지 추가 테스트 (add_messages annotation)"""
        initial_state = AIState(
            user_id="test_user",
            messages=[{"role": "user", "content": "첫 메시지"}],
            current_week="2026-W17"
        )

        # add_messages를 통한 메시지 누적
        new_messages = [{"role": "assistant", "content": "응답"}]
        updated = initial_state.copy()
        updated.messages.extend(new_messages)

        assert len(updated.messages) == 2, "메시지가 추가되지 않음"
        assert updated.messages[1]["role"] == "assistant", "응답 메시지가 추가되지 않음"

    def test_ai_state_with_tool_results(self):
        """Tool 결과 저장 테스트"""
        state = AIState(
            user_id="test_user",
            messages=[],
            current_week="2026-W17",
            tool_results={
                "analyze_character_earnings": {
                    "success": True,
                    "earnings_trend": [1000000, 1100000]
                }
            }
        )

        assert "analyze_character_earnings" in state.tool_results, "tool_results에 키가 없음"
        assert state.tool_results["analyze_character_earnings"]["success"] is True, "tool 결과가 잘못됨"

    def test_ai_state_with_user_context(self):
        """사용자 컨텍스트 저장 테스트"""
        state = AIState(
            user_id="test_user",
            messages=[],
            current_week="2026-W17",
            user_context={
                "character_level": 250,
                "class": "아크메이지(불,독)"
            }
        )

        assert state.user_context["character_level"] == 250, "user_context가 저장되지 않음"
        assert state.user_context["class"] == "아크메이지(불,독)", "class가 저장되지 않음"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
