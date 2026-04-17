"""
AI Service - LangGraph 기반 AI Agent
"""
import logging
from datetime import datetime
from typing import AsyncIterator
from app.ai.state import AIState
from app.ai.graph import create_ai_graph
from app.ai.tools.character_tools import (
    replicate_checklist_from_last_week,
    analyze_character_earnings,
    get_character_checklist
)
from app.ai.tools.earnings_tools import (
    analyze_user_earnings,
    get_top_earning_bosses
)

logger = logging.getLogger(__name__)


class AIService:
    """LangGraph 기반 AI Service"""

    def __init__(self, char_service, user_service, data_service):
        """
        서비스 초기화.

        Args:
            char_service: CharacterService 인스턴스
            user_service: UserService 인스턴스
            data_service: 데이터 서비스 인스턴스
        """
        self.char_service = char_service
        self.user_service = user_service
        self.data_service = data_service

        # LangChain Tools 리스트
        self.tools = [
            replicate_checklist_from_last_week,
            analyze_character_earnings,
            get_character_checklist,
            analyze_user_earnings,
            get_top_earning_bosses
        ]

        # Tool 이름 → 함수 매핑
        self.tools_dict = {
            tool.name: tool for tool in self.tools
        }

        # 그래프 생성
        self.graph = create_ai_graph(
            tools=self.tools,
            tools_dict=self.tools_dict,
            char_service=char_service,
            user_service=user_service,
            data_service=data_service
        )

        logger.info("AIService initialized")

    def get_current_week_key(self) -> str:
        """
        현재 주차를 YYYY-Www 형식으로 계산.
        """
        now = datetime.now()
        jan4 = datetime(now.year, 1, 4)
        week_one = datetime.fromordinal(jan4.toordinal() - jan4.weekday())
        days_diff = (now - week_one).days
        week = (days_diff // 7) + 1
        return f"{now.year}-W{week:02d}"

    async def chat(self, user_id: str, message: str, char_name: str = None) -> str:
        """
        사용자 메시지 처리.

        Args:
            user_id: 사용자 ID
            message: 사용자 메시지
            char_name: 캐릭터 이름 (선택)

        Returns:
            AI 응답
        """
        try:
            logger.info(f"Chat request: user={user_id}, message={message[:50]}")

            # 초기 State 생성
            current_week = self.get_current_week_key()

            initial_state = AIState(
                user_id=user_id,
                char_name=char_name,
                messages=[{
                    "role": "user",
                    "content": message
                }],
                current_week=current_week
            )

            # 그래프 실행
            final_state = await self.graph.ainvoke(initial_state)

            # 최종 응답 추출
            response = final_state.get("final_response", "응답을 생성할 수 없습니다")

            logger.info(f"Chat response: {response[:100]}")

            return response

        except Exception as e:
            logger.error(f"Error in chat: {str(e)}", exc_info=True)
            return f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}"

    async def chat_streaming(
        self,
        user_id: str,
        message: str,
        char_name: str = None
    ) -> AsyncIterator[dict]:
        """
        스트리밍 응답 제공.

        Args:
            user_id: 사용자 ID
            message: 사용자 메시지
            char_name: 캐릭터 이름 (선택)

        Yields:
            각 노드 실행 결과
        """
        try:
            logger.info(f"Chat streaming: user={user_id}, message={message[:50]}")

            current_week = self.get_current_week_key()

            initial_state = AIState(
                user_id=user_id,
                char_name=char_name,
                messages=[{
                    "role": "user",
                    "content": message
                }],
                current_week=current_week
            )

            # 스트리밍 실행
            async for event in self.graph.astream(initial_state):
                yield event

        except Exception as e:
            logger.error(f"Error in chat_streaming: {str(e)}", exc_info=True)
            yield {
                "error": True,
                "message": f"스트리밍 중 오류: {str(e)}"
            }
