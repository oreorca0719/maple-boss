"""
최종 응답 생성 노드
"""
import json
import logging
from typing import Any
from langchain_core.messages import AIMessage, BaseMessage
from app.ai.state import AIState

logger = logging.getLogger(__name__)


def output_node(state: AIState) -> dict[str, Any]:
    """
    최종 응답을 생성하는 노드.
    Tool 실행 결과가 있으면 함께 표시합니다.
    """

    try:
        # 마지막 메시지 찾기
        if not state.messages:
            return {
                "final_response": "죄송합니다. 응답을 생성할 수 없습니다."
            }

        # 역순으로 마지막 assistant 메시지 찾기
        last_assistant_message = None
        for msg in reversed(state.messages):
            # BaseMessage 객체인 경우
            if isinstance(msg, BaseMessage):
                if isinstance(msg, AIMessage):
                    last_assistant_message = msg
                    break
            # 딕셔너리인 경우
            elif isinstance(msg, dict) and msg.get("role") == "assistant":
                last_assistant_message = msg
                break

        if not last_assistant_message:
            return {
                "final_response": "죄송합니다. 응답을 생성할 수 없습니다."
            }

        # BaseMessage 객체인 경우 처리
        if isinstance(last_assistant_message, BaseMessage):
            response_text = last_assistant_message.content
        # LangChain 메시지 객체인 경우 처리
        elif hasattr(last_assistant_message, "content"):
            response_text = last_assistant_message.content
        elif isinstance(last_assistant_message, dict):
            response_text = last_assistant_message.get("content", "")
        else:
            response_text = str(last_assistant_message)

        # Tool 결과가 있으면 추가 정보 표시
        if state.tool_results:
            logger.info(f"Tool results available: {list(state.tool_results.keys())}")
            # Tool 결과는 LLM이 이미 응답에 포함시켰으므로,
            # 여기서는 추가 처리 없음

        logger.info(f"Final response generated: {response_text[:100]}")

        return {
            "final_response": response_text,
            "user_context": {
                **state.user_context,
                "tools_used": list(state.tool_results.keys()) if state.tool_results else []
            }
        }

    except Exception as e:
        logger.error(f"Error in output_node: {str(e)}", exc_info=True)
        return {
            "final_response": f"응답 생성 중 오류가 발생했습니다: {str(e)}"
        }
